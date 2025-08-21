#!/usr/bin/env python3
"""
Card Play Inference Program
Uses Ben's card playing models to predict the next card to play given game state.
"""

import sys
import os
import argparse
import numpy as np
import time
import json

# Set environment variables before importing TensorFlow
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

# Suppress warnings
import warnings
warnings.filterwarnings('ignore')

import tensorflow as tf

# Add parent directory to path to import Ben modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)
sys.path.insert(0, os.path.join(parent_dir, 'src'))

from nn.player_tf2 import BatchPlayer
import binary
import deck52
from bidding import bidding
from util import hand_to_str, follow_suit

class PlayInference:
    def __init__(self, model_path=None, model_overrides=None, silent=False):
        """
        Initialize the card play inference system.
        
        Args:
            model_path: Path to the card playing model file (deprecated - use role-based selection)
            model_overrides: Dict of model overrides for specific roles
            silent: Suppress loading messages
        """
        self.model_path = model_path
        self.model_overrides = model_overrides or {}
        
        # Default model paths (latest versions, ignoring Jack models)
        self.default_models = {
            'lefty_nt': 'models/TF2models/lefty_nt_2024-07-08-E20.keras',
            'dummy_nt': 'models/TF2models/dummy_nt_2024-07-08-E20.keras', 
            'righty_nt': 'models/TF2models/righty_nt_2024-07-16-E20.keras',
            'decl_nt': 'models/TF2models/decl_nt_2024-07-08-E20.keras',
            'lefty_suit': 'models/TF2models/lefty_suit_2024-07-08-E20.keras',
            'dummy_suit': 'models/TF2models/dummy_suit_2024-07-08-E20.keras',
            'righty_suit': 'models/TF2models/righty_suit_2024-07-16-E20.keras', 
            'decl_suit': 'models/TF2models/decl_suit_2024-07-08-E20.keras'
        }
        
        # Apply overrides
        self.models = {**self.default_models, **self.model_overrides}
        
        # Will be set when we know the role and contract type
        self.player = None
        
        # Check TensorFlow version
        self.tf_version = tf.__version__
        self.silent = silent
        if not silent:
            print(f"TensorFlow version: {self.tf_version}")
        
        # Legacy support: if model_path provided, load it immediately
        if model_path:
            self._load_model(model_path)
    
    def _load_model(self, model_path):
        """Load a specific model."""
        if not self.silent:
            print(f"Loading model from {model_path}...")
        load_start = time.time()
        
        # Check if file exists and is accessible
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        # Use absolute path
        model_path = os.path.abspath(model_path)
        
        try:
            self.player = BatchPlayer("PlayModel", model_path)
            load_time = time.time() - load_start
            if not self.silent:
                print(f"Model loaded in {load_time:.2f} seconds")
        except Exception as e:
            if not self.silent:
                print(f"\nError loading model: {e}")
                print("\nPossible solutions:")
                print("1. Upgrade TensorFlow: pip install tensorflow>=2.12")
                print("2. Check that the model file is not corrupted")
            raise
    
    def _get_bridge_role(self, player_position, declarer_position, auction, opening_lead):
        """
        Determine bridge role based on positions and auction.
        
        Returns:
            String: 'lefty', 'dummy', 'righty', or 'decl'
        """
        player_pos = self.get_position_offset(player_position)
        declarer_pos = self.get_position_offset(declarer_position)
        dummy_pos = (declarer_pos + 2) % 4  # Dummy is declarer's partner
        
        # Declarer position is provided directly
        
        # Determine role based on relative position to declarer
        # In bridge: LHO = Left Hand Opponent (next player clockwise)
        #           RHO = Right Hand Opponent (previous player clockwise)
        if player_pos == declarer_pos:
            return 'decl'
        elif player_pos == dummy_pos:
            return 'dummy'
        elif player_pos == (declarer_pos + 1) % 4:  # Next player clockwise = LHO
            return 'lefty'
        elif player_pos == (declarer_pos + 3) % 4:  # Previous player clockwise = RHO  
            return 'righty'
        else:
            raise ValueError(f"Unable to determine role for player {player_position}")
    
    def _ensure_model_loaded(self, player_position, declarer_position, contract, auction, opening_lead):
        """Ensure the correct model is loaded for this scenario."""
        if self.player is not None:
            return  # Model already loaded
        
        # Determine bridge role and contract type
        role = self._get_bridge_role(player_position, declarer_position, auction, opening_lead)
        _, strain_i = self.parse_contract(contract)
        contract_type = 'nt' if strain_i == 0 else 'suit'
        
        # Note: Dedicated opening lead models (Lead-NT/Lead-Suit) use different input format
        # and cannot be used as drop-in replacements. They require binary.get_auction_binary_for_lead()
        # instead of the 298-feature format used by regular card playing models.
        
        # Select appropriate model
        model_key = f"{role}_{contract_type}"
        model_path = self.models[model_key]
        
        if not self.silent:
            print(f"Auto-selected {model_key} model: {os.path.basename(model_path)}")
            if opening_lead and role == 'lefty':
                print(f"Note: Using general lefty model for opening lead. Dedicated Lead-{contract_type.upper()} models require different input format.")
        
        self.selected_model = model_path
        self.selected_role = f"{role}_{contract_type}"
        self._load_model(model_path)
    
    def parse_hand(self, hand_str):
        """
        Parse hand string into binary format.
        
        Args:
            hand_str: Hand in PBN format (e.g., "AKQ.JT9.8765.432")
        
        Returns:
            32-element binary array representing the hand
        """
        return binary.parse_hand_f(32)(hand_str).reshape(32)
    
    def parse_contract(self, contract_str):
        """
        Parse contract string.
        
        Args:
            contract_str: Contract (e.g., "3NT", "4S", "6C")
        
        Returns:
            tuple of (level, strain_i) where strain_i: 0=NT, 1=S, 2=H, 3=D, 4=C
        """
        contract_str = contract_str.upper()
        level = int(contract_str[0])
        strain_str = contract_str[1:]
        
        strain_map = {'NT': 0, 'S': 1, 'H': 2, 'D': 3, 'C': 4, 'N': 0}
        if strain_str not in strain_map:
            raise ValueError(f"Unknown strain: {strain_str}")
        
        return level, strain_map[strain_str]
    
    def parse_cards_played(self, cards_str):
        """
        Parse cards played string into tricks.
        
        Args:
            cards_str: Space-separated cards (e.g., "CK CA C2 C3 ST SJ SQ SA")
        
        Returns:
            List of tricks, each trick is a list of 4 cards in 52-card format
        """
        if not cards_str:
            return []
        
        cards = cards_str.strip().upper().split()
        tricks = []
        
        # Group cards into tricks of 4
        for i in range(0, len(cards), 4):
            if i + 3 < len(cards):
                trick = []
                for j in range(4):
                    card_str = cards[i + j]
                    if len(card_str) != 2:
                        raise ValueError(f"Invalid card format: {card_str}")
                    card52 = deck52.encode_card(card_str)
                    trick.append(card52)
                tricks.append(trick)
            else:
                # Incomplete trick - current trick in progress
                current_trick = []
                for j in range(len(cards) - i):
                    card_str = cards[i + j]
                    if len(card_str) != 2:
                        raise ValueError(f"Invalid card format: {card_str}")
                    card52 = deck52.encode_card(card_str)
                    current_trick.append(card52)
                tricks.append(current_trick)
        
        return tricks
    
    def get_position_offset(self, position):
        """Get position offset (0=N, 1=E, 2=S, 3=W)"""
        position = position.upper()
        if position in ['N', 'NORTH', '0']:
            return 0
        elif position in ['E', 'EAST', '1']:
            return 1
        elif position in ['S', 'SOUTH', '2']:
            return 2
        elif position in ['W', 'WEST', '3']:
            return 3
        else:
            raise ValueError(f"Unknown position: {position}")
    
    def parse_auction(self, auction_str):
        """
        Parse auction string into list of bids.
        
        Args:
            auction_str: Space-separated string of bids (e.g., "1C PASS 1H X")
        
        Returns:
            List of bids
        """
        if not auction_str:
            return []
        
        # Convert common bid formats
        bids = []
        for bid in auction_str.strip().upper().split():
            # Handle special bids
            if bid in ['P', 'PASS']:
                bids.append('PASS')
            elif bid in ['X', 'DBL', 'DOUBLE', 'D']:
                bids.append('X')
            elif bid in ['XX', 'RDBL', 'REDOUBLE', 'RD', 'R']:
                bids.append('XX')
            else:
                # Convert 10 to T in standard bids
                bid = bid.replace('10', 'T')
                bids.append(bid)
        
        return bids
    
    
    def create_x_play(self, player_hand32, dummy_hand32, level, strain_i, tricks, current_trick, player_pos, dummy_pos, leader_positions, dummy_visible, declarer_pos):
        """
        Create the input tensor for the playing model.
        
        Args:
            player_hand32: 32-element binary array for player's hand
            dummy_hand32: 32-element binary array for dummy's hand  
            level: Contract level (1-7)
            strain_i: Strain index (0=NT, 1=S, 2=H, 3=D, 4=C)
            tricks: List of completed tricks
            current_trick: Current trick in progress (list of cards)
            player_pos: Player's position (0-3)
            dummy_pos: Dummy's position (0-3)
            leader_positions: List of leader positions for each trick
            dummy_visible: Whether dummy is visible
        
        Returns:
            x_play tensor of shape (1, n_tricks, 298)
        """
        n_tricks_completed = len(tricks)
        n_tricks_total = n_tricks_completed + (1 if current_trick else 0)
        
        if n_tricks_total == 0:
            n_tricks_total = 1  # At least one trick for opening lead
        
        x_play = np.zeros((1, n_tricks_total, 298), dtype=np.float16)
        
        # Set initial state (trick 0)
        binary.BinaryInput(x_play[:, 0, :]).set_player_hand(player_hand32)
        
        # Set dummy hand based on visibility and player role
        if dummy_visible and (player_pos == dummy_pos or player_pos == declarer_pos or n_tricks_completed > 0):
            # Dummy is visible to declarer, dummy, or after opening lead
            if player_pos == dummy_pos:
                # We are dummy - public hand should be declarer's (but we don't have it, use zeros)
                binary.BinaryInput(x_play[:, 0, :]).set_public_hand(np.zeros(32))
            else:
                # We can see dummy
                binary.BinaryInput(x_play[:, 0, :]).set_public_hand(dummy_hand32)
        else:
            # Dummy not visible (opening lead by defenders)
            binary.BinaryInput(x_play[:, 0, :]).set_public_hand(np.zeros(32))
        
        # Set contract information
        x_play[:, 0, 292] = level
        x_play[:, 0, 293 + strain_i] = 1
        
        # Add completed tricks
        for trick_idx, trick in enumerate(tricks):
            if trick_idx + 1 >= n_tricks_total:
                break
                
            # Copy previous state
            x_play[:, trick_idx + 1, :] = x_play[:, trick_idx, :]
            
            # Set the cards played in this trick
            leader_pos = leader_positions[trick_idx] if trick_idx < len(leader_positions) else 0
            
            for card_idx, card52 in enumerate(trick):
                if card_idx >= 4:
                    break
                    
                position_in_trick = (leader_pos + card_idx) % 4
                card32 = deck52.card52to32(card52)
                
                # Set the card in the current trick using the correct offset calculation
                # offset is relative to the current player (player_pos)
                offset = (player_pos - position_in_trick) % 4  # 1 = rho, 2 = partner, 3 = lho
                if offset > 0:  # Don't set our own card in the trick representation
                    trick_offset = 192 + (3 - offset) * 32
                    x_play[:, trick_idx + 1, trick_offset + card32] = 1
                
                # Remove card from appropriate hand
                if position_in_trick == player_pos:
                    x_play[:, trick_idx + 1, card32] = 0
                elif position_in_trick == dummy_pos and player_pos != dummy_pos and dummy_visible:
                    x_play[:, trick_idx + 1, 32 + card32] = 0
        
        # Add current trick if it exists
        if current_trick and n_tricks_completed < n_tricks_total:
            trick_idx = n_tricks_completed
            
            # Copy previous state
            if trick_idx > 0:
                x_play[:, trick_idx, :] = x_play[:, trick_idx - 1, :]
            
            # Set cards played so far in current trick
            leader_pos = leader_positions[trick_idx] if trick_idx < len(leader_positions) else 0
            
            for card_idx, card52 in enumerate(current_trick):
                position_in_trick = (leader_pos + card_idx) % 4
                card32 = deck52.card52to32(card52)
                
                # Set the card in the current trick using the correct offset calculation
                # offset is relative to the current player (player_pos)  
                offset = (player_pos - position_in_trick) % 4  # 1 = rho, 2 = partner, 3 = lho
                if offset > 0:  # Don't set our own card in the trick representation
                    trick_offset = 192 + (3 - offset) * 32
                    x_play[:, trick_idx, trick_offset + card32] = 1
                
                # Remove card from appropriate hand
                if position_in_trick == player_pos:
                    x_play[:, trick_idx, card32] = 0
                elif position_in_trick == dummy_pos and player_pos != dummy_pos and dummy_visible:
                    x_play[:, trick_idx, 32 + card32] = 0
        
        return x_play
    
    def predict_next_card(self, player_hand, dummy_hand, contract, tricks_played, current_trick, player_position, declarer_position, auction=None, opening_lead=False):
        """
        Predict the next card to play.
        
        Args:
            player_hand: Player's hand in PBN format
            dummy_hand: Dummy's hand in PBN format (if visible, empty for opening lead)
            contract: Contract string (e.g., "3NT")
            tricks_played: String of completed tricks (space-separated cards)
            current_trick: String of current trick cards (space-separated)
            player_position: Player's position ('N', 'E', 'S', 'W')
            declarer_position: Declarer's position ('N', 'E', 'S', 'W')
            auction: Auction history (optional for context)
            opening_lead: True if this is the opening lead (dummy not visible yet)
        
        Returns:
            Dictionary with card predictions and probabilities
        """
        # Ensure correct model is loaded for this scenario
        self._ensure_model_loaded(player_position, declarer_position, contract, auction, opening_lead)
        
        # Parse inputs
        player_hand32 = self.parse_hand(player_hand)
        declarer_pos = self.get_position_offset(declarer_position)
        dummy_pos = (declarer_pos + 2) % 4  # Dummy is declarer's partner
        
        # Handle opening lead case - dummy not visible yet
        if opening_lead or not dummy_hand:
            dummy_hand32 = np.zeros(32)
            dummy_visible = False
        else:
            dummy_hand32 = self.parse_hand(dummy_hand)
            dummy_visible = True
        
        level, strain_i = self.parse_contract(contract)
        
        # Parse tricks
        all_tricks = self.parse_cards_played(tricks_played) if tricks_played else []
        current_trick_cards = self.parse_cards_played(current_trick) if current_trick else []
        current_trick_list = current_trick_cards[0] if current_trick_cards else []
        
        # Get position offsets
        player_pos = self.get_position_offset(player_position)
        
        # Calculate leader positions for each trick (simplified - assume North leads first trick)
        leader_positions = []
        current_leader = 0  # North leads first trick typically
        
        for trick_idx in range(len(all_tricks) + (1 if current_trick_list else 0)):
            leader_positions.append(current_leader)
            # Winner of previous trick leads next (simplified logic)
            current_leader = (current_leader + 1) % 4  # Simplified - in real game, winner leads
        
        # Create input tensor
        x_play = self.create_x_play(
            player_hand32, dummy_hand32, level, strain_i,
            all_tricks, current_trick_list, player_pos, dummy_pos, leader_positions, dummy_visible, declarer_pos
        )
        
        # Make prediction
        inference_start = time.time()
        
        # Get current trick index
        trick_i = len(all_tricks)
        if current_trick_list:
            trick_i = len(all_tricks)
        
        # Use the model to get card probabilities
        cards_softmax = self.player.next_cards_softmax(x_play[:, :(trick_i + 1), :])
        
        # Apply legal card constraints (follow suit if required)
        if trick_i < x_play.shape[1]:
            current_hand = binary.BinaryInput(x_play[:, trick_i, :]).get_player_hand()
            
            # Determine lead suit from current trick
            if current_trick_list:
                lead_card52 = current_trick_list[0]
                lead_suit_i = lead_card52 // 13
                # Create one-hot encoded lead suit (shape: 1, 4)
                lead_suit = np.zeros((1, 4))
                lead_suit[0, lead_suit_i] = 1
                
                # Apply follow suit constraint
                legal_cards = follow_suit(
                    cards_softmax,
                    current_hand,
                    lead_suit
                )
            else:
                legal_cards = cards_softmax.copy()
                # Mask out cards not in hand
                for i in range(32):
                    if current_hand[0, i] == 0:
                        legal_cards[0, i] = 0
        else:
            legal_cards = cards_softmax
        
        inference_time = time.time() - inference_start
        
        # Normalize probabilities
        legal_cards_flat = legal_cards.reshape(-1)
        if np.sum(legal_cards_flat) > 0:
            legal_cards_flat = legal_cards_flat / np.sum(legal_cards_flat)
        
        # Get top 5 cards
        top_k = min(5, np.sum(legal_cards_flat > 0))
        top_indices = np.argsort(legal_cards_flat)[-top_k:][::-1]
        
        # Convert card indices to card strings
        results = {
            'recommended_card': None,
            'recommended_card_prob': 0.0,
            'top_cards': [],
            'inference_time': inference_time,
            'all_card_probs': legal_cards_flat
        }
        
        if top_k > 0:
            top_card32 = top_indices[0]
            top_card52 = deck52.card32to52(top_card32)
            results['recommended_card'] = deck52.decode_card(top_card52)
            results['recommended_card_prob'] = float(legal_cards_flat[top_card32])
            
            for idx in top_indices:
                if legal_cards_flat[idx] > 0:
                    card32 = idx
                    card52 = deck52.card32to52(card32)
                    card_str = deck52.decode_card(card52)
                    prob = float(legal_cards_flat[idx])
                    results['top_cards'].append({'card': card_str, 'probability': prob})
        
        return results


def main():
    parser = argparse.ArgumentParser(description='Ben Card Play Inference - Predict next card using neural network models')
    
    # Required arguments
    parser.add_argument('hand', help='Player hand in PBN format (e.g., "AKQ.JT9.8765.432")')
    parser.add_argument('contract', help='Contract (e.g., "3NT", "4S")')
    parser.add_argument('--position', required=True, help='Player position: N=North, E=East, S=South, W=West')
    parser.add_argument('--declarer-position', required=True, help='Declarer position: N, E, S, W')
    
    # Model override options (optional)
    parser.add_argument('--model', help='Specify model path (overrides auto-selection)')
    parser.add_argument('--lefty-nt-model', help='Override lefty NT model')
    parser.add_argument('--dummy-nt-model', help='Override dummy NT model') 
    parser.add_argument('--righty-nt-model', help='Override righty NT model')
    parser.add_argument('--decl-nt-model', help='Override declarer NT model')
    parser.add_argument('--lefty-suit-model', help='Override lefty suit model')
    parser.add_argument('--dummy-suit-model', help='Override dummy suit model')
    parser.add_argument('--righty-suit-model', help='Override righty suit model')
    parser.add_argument('--decl-suit-model', help='Override declarer suit model')
    
    # Optional arguments
    parser.add_argument('--dummy-hand', default='', help='Dummy hand in PBN format (if visible, leave empty for opening lead)')
    parser.add_argument('--tricks-played', default='', help='Completed tricks as space-separated cards (e.g., "CK CA C2 C3 ST SJ SQ SA")')
    parser.add_argument('--current-trick', default='', help='Current trick cards (space-separated)')
    parser.add_argument('--auction', default='', help='Auction history (required for opening lead or when dummy not provided)')
    parser.add_argument('--opening-lead', action='store_true', help='This is the opening lead (dummy not visible yet)')
    parser.add_argument('--json', action='store_true', help='Output in JSON format for programmatic use')
    parser.add_argument('--verbose', action='store_true', help='Show detailed human-readable output (default without --json)')
    
    args = parser.parse_args()
    
    # Determine output settings
    show_human_output = not args.json and (args.verbose or True)
    
    # Build model overrides dictionary
    model_overrides = {}
    if args.lefty_nt_model:
        model_overrides['lefty_nt'] = args.lefty_nt_model
    if args.dummy_nt_model:
        model_overrides['dummy_nt'] = args.dummy_nt_model
    if args.righty_nt_model:
        model_overrides['righty_nt'] = args.righty_nt_model
    if args.decl_nt_model:
        model_overrides['decl_nt'] = args.decl_nt_model
    if args.lefty_suit_model:
        model_overrides['lefty_suit'] = args.lefty_suit_model
    if args.dummy_suit_model:
        model_overrides['dummy_suit'] = args.dummy_suit_model
    if args.righty_suit_model:
        model_overrides['righty_suit'] = args.righty_suit_model
    if args.decl_suit_model:
        model_overrides['decl_suit'] = args.decl_suit_model
    
    # Create inference object
    try:
        inference = PlayInference(
            model_path=args.model,  # Legacy support
            model_overrides=model_overrides,
            silent=args.json
        )
    except Exception as e:
        if args.json:
            error_output = {
                "error": str(e),
                "success": False
            }
            print(json.dumps(error_output, indent=2))
        else:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Make prediction
    try:
        result = inference.predict_next_card(
            player_hand=args.hand,
            dummy_hand=args.dummy_hand,
            contract=args.contract,
            tricks_played=args.tricks_played,
            current_trick=args.current_trick,
            player_position=args.position,
            declarer_position=args.declarer_position,
            auction=args.auction,
            opening_lead=args.opening_lead
        )
        
        if args.json:
            # Structured JSON output
            json_output = {
                "success": True,
                "input": {
                    "hand": args.hand,
                    "dummy_hand": args.dummy_hand if args.dummy_hand else None,
                    "contract": args.contract,
                    "position": args.position,
                    "declarer_position": args.declarer_position,
                    "tricks_played": args.tricks_played if args.tricks_played else None,
                    "current_trick": args.current_trick if args.current_trick else None,
                    "model": os.path.basename(getattr(inference, 'selected_model', args.model or 'auto-selected')),
                    "model_role": getattr(inference, 'selected_role', 'unknown')
                },
                "result": {
                    "recommended_card": result['recommended_card'],
                    "confidence": round(result['recommended_card_prob'], 4),
                    "cards": [
                        {
                            "card": card_info['card'],
                            "probability": round(card_info['probability'], 4)
                        }
                        for card_info in result['top_cards']
                    ],
                    "metrics": {
                        "inference_time_seconds": round(result['inference_time'], 3)
                    }
                }
            }
            
            print(json.dumps(json_output, indent=2))
        
        if show_human_output:
            # Human-readable output
            print(f"\nPlayer Hand: {args.hand}")
            if args.dummy_hand:
                print(f"Dummy Hand: {args.dummy_hand}")
            print(f"Contract: {args.contract}")
            print(f"Position: {args.position}")
            print(f"Declarer Position: {args.declarer_position}")
            if args.tricks_played:
                print(f"Tricks Played: {args.tricks_played}")
            if args.current_trick:
                print(f"Current Trick: {args.current_trick}")
            
            print(f"\n{'='*50}")
            if result['recommended_card']:
                print(f"Recommended card: {result['recommended_card']} ({result['recommended_card_prob']:.1%})")
                
                print(f"\nTop card options:")
                for i, card_info in enumerate(result['top_cards'], 1):
                    print(f"  {i}. {card_info['card']:3s} - {card_info['probability']:.1%}")
            else:
                print("No valid cards found")
            
            if args.verbose:
                print(f"\nTiming:")
                print(f"  Inference time: {result['inference_time']:.3f} seconds")
            
    except Exception as e:
        if args.json:
            error_output = {
                "error": str(e),
                "success": False,
                "input": {
                    "hand": args.hand,
                    "contract": args.contract,
                    "position": args.position,
                    "declarer_position": args.declarer_position,
                    "model": os.path.basename(getattr(inference, 'selected_model', args.model or 'auto-selected'))
                }
            }
            print(json.dumps(error_output, indent=2))
        else:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()