#!/usr/bin/env python3
"""
Bidding Inference Program
Uses Ben's bidding models to predict the next bid given a hand and auction.
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
from tensorflow.keras.models import load_model

# Add parent directory to path to import Ben modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)
sys.path.insert(0, os.path.join(parent_dir, 'src'))

from nn.bidder_tf2 import Bidder
import binary
from bidding import bidding

class BiddingInference:
    def __init__(self, model_path, n_cards=32, model_version=3, alert_supported=False, silent=False):
        """
        Initialize the bidding inference system.
        
        Args:
            model_path: Path to the bidding model file
            n_cards: Number of cards to use (32 or 52)
            model_version: Model version (0, 1, 2, or 3)
            alert_supported: Whether the model supports alerts
            silent: Suppress loading messages
        """
        self.n_cards = n_cards
        self.model_version = model_version
        self.alert_supported = alert_supported
        
        # Check TensorFlow version
        tf_version = tf.__version__
        if not silent:
            print(f"TensorFlow version: {tf_version}")
        
        # Load the bidding model
        if not silent:
            print(f"Loading model from {model_path}...")
        load_start = time.time()
        
        # Check if file exists and is accessible
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        # Use absolute path
        model_path = os.path.abspath(model_path)
        
        # Check if we need to handle Keras 3.x format with older TF
        if not silent and tf_version.startswith('2.') and int(tf_version.split('.')[1]) < 12:
            print("Note: Using TensorFlow < 2.12, model loading may require Keras 3.x format support")
            print("If model loading fails, please upgrade TensorFlow: pip install tensorflow>=2.12")
        
        try:
            self.bidder = Bidder("BiddingModel", model_path, alert_supported)
            load_time = time.time() - load_start
            if not silent:
                print(f"Model loaded in {load_time:.2f} seconds")
        except Exception as e:
            if not silent:
                print(f"\nError loading model: {e}")
                print("\nPossible solutions:")
                print("1. Upgrade TensorFlow: pip install tensorflow>=2.12")
                print("2. The model file may be in Keras 3.x format which requires newer TensorFlow")
                print("3. Check that the model file is not corrupted")
            raise
        
        # Create a simple models object with required attributes
        self.models = type('Models', (), {
            'n_cards_bidding': n_cards,
            'model_version': model_version,
            'ns': 0.5,  # Default NS system indicator
            'ew': 0.5,  # Default EW system indicator
            'adjust_hcp': False  # Default: don't adjust HCP
        })()
        
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
    
    def parse_vulnerability(self, vuln_str):
        """
        Parse vulnerability string.
        
        Args:
            vuln_str: Vulnerability description (e.g., "None", "NS", "EW", "Both", "All")
        
        Returns:
            Tuple of (NS_vuln, EW_vuln) as booleans
        """
        vuln_str = vuln_str.upper()
        
        if vuln_str in ['NONE', 'N', '-']:
            return (False, False)
        elif vuln_str in ['NS', 'N-S']:
            return (True, False)
        elif vuln_str in ['EW', 'E-W']:
            return (False, True)
        elif vuln_str in ['BOTH', 'ALL', 'B']:
            return (True, True)
        else:
            raise ValueError(f"Unknown vulnerability: {vuln_str}")
    
    def get_position_offset(self, position):
        """
        Get the position offset for the auction.
        
        Args:
            position: Position ('N', 'E', 'S', 'W')
        
        Returns:
            Offset (0-3)
        """
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
    
    def predict_bid(self, hand_str, auction, vuln, dealer='N', seat='N'):
        """
        Predict the next bid given a hand and auction.
        
        Args:
            hand_str: Hand in PBN format (e.g., "AKQ.JT9.8765.432")
            auction: List of bids or space-separated string
            vuln: Vulnerability tuple or string
            dealer: Dealer position ('N', 'E', 'S', 'W')
            seat: Seat of the hand ('N', 'E', 'S', 'W')
        
        Returns:
            Dictionary with bid predictions and probabilities
        """
        # Parse inputs
        if isinstance(auction, str):
            auction = self.parse_auction(auction)
        
        if isinstance(vuln, str):
            vuln = self.parse_vulnerability(vuln)
        
        # Get position offsets
        dealer_offset = self.get_position_offset(dealer)
        seat_offset = self.get_position_offset(seat)
        
        # Calculate hand index - using full auction length modulo 4 (following botbidder.py)
        # This is NOT relative to dealer, but the absolute position in the current bidding round
        hand_ix_relative = (seat_offset - dealer_offset) % 4  # Keep for validation
        
        # Adjust auction for dealer by padding with PAD_START
        # This ensures the auction aligns with the dealer position
        full_auction = ['PAD_START'] * dealer_offset + auction
        
        # Calculate whose turn it is based on total auction length
        next_to_bid_position = len(full_auction) % 4
        
        # Check if it's the correct seat's turn
        if next_to_bid_position != seat_offset:
            # Calculate which seat should be bidding
            seats = ['N', 'E', 'S', 'W']
            expected_seat = seats[next_to_bid_position]
            raise ValueError(f"It's not {seat}'s turn to bid. Expected {expected_seat} to bid (auction: {auction}, dealer: {dealer})")
        
        # Parse hand
        hand_binary = binary.parse_hand_f(self.n_cards)(hand_str)
        
        # Calculate number of bidding rounds
        # Following the logic from botbidder.py get_bid_number_for_player_to_bid
        hand_i = len(full_auction) % 4
        i = hand_i
        while i < len(full_auction) and full_auction[i] == 'PAD_START':
            i += 4
        n_steps = 1 + (len(full_auction) - i) // 4
        
        # Use auction length for hand_ix (following botbidder.py line 99)
        hand_ix = len(full_auction) % 4
        
        # Get binary representation of auction
        # hand_ix is the position in the current round (0-3)
        X = binary.get_auction_binary(n_steps, full_auction, hand_ix, hand_binary, vuln, self.models)
        
        # Make prediction
        inference_start = time.time()
        bids_output, alerts = self.bidder.pred_fun_seq(X)
        
        # The model outputs are already probabilities (they sum to 1), NOT logits!
        # Don't apply softmax again
        bids_probs = bids_output
        inference_time = time.time() - inference_start
        
        # Get the last step's predictions (current bidding round)
        current_probs = bids_probs[0, -1, :]
        
        # Get top 5 bids
        top_k = 5
        top_indices = np.argsort(current_probs)[-top_k:][::-1]
        
        # Debug: Check the total probability mass in top bids
        total_top_prob = np.sum(current_probs[top_indices])
        max_prob = np.max(current_probs)
        
        results = {
            'top_bid': bidding.ID2BID[top_indices[0]],
            'top_bid_prob': float(current_probs[top_indices[0]]),
            'top_bids': [],
            'max_prob': float(max_prob),
            'total_top_5_prob': float(total_top_prob),
            'entropy': float(-np.sum(current_probs * np.log(current_probs + 1e-8))),  # Information entropy
            'inference_time': inference_time,
            'current_probs': current_probs  # Store all probabilities for JSON output
        }
        
        for idx in top_indices:
            bid = bidding.ID2BID[idx]
            prob = float(current_probs[idx])
            results['top_bids'].append({'bid': bid, 'probability': prob})
        
        # Add alert information if supported
        if self.alert_supported and alerts is not None:
            alert_probs = alerts[0, -1, :]
            results['alert_probability'] = float(alert_probs[top_indices[0]])
        
        return results


def main():
    parser = argparse.ArgumentParser(description='Ben Bidding Inference - Predict bids using neural network models')
    
    # Required arguments
    parser.add_argument('hand', help='Hand in PBN format (e.g., "AKQ.JT9.8765.432")')
    parser.add_argument('model', help='Path to bidding model file (e.g., models/TF2models/BEN-Sayc-8730_2025-04-20-E30.keras)')
    
    # Optional arguments
    parser.add_argument('--auction', default='', help='Space-separated auction (e.g., "1C PASS 1H PASS")')
    parser.add_argument('--vuln', default='None', help='Vulnerability: None, NS, EW, Both/All')
    parser.add_argument('--dealer', default='N', help='Dealer: N, E, S, W')
    parser.add_argument('--seat', default='N', help='Seat of hand: N=North, E=East, S=South, W=West')
    parser.add_argument('--n-cards', type=int, default=32, choices=[24, 32, 52], 
                       help='Number of cards in model (24 for bidding with grouped pips, 32 for play, 52 for full deck)')
    parser.add_argument('--model-version', type=int, default=3, choices=[0, 1, 2, 3], help='Model version')
    parser.add_argument('--alert-supported', action='store_true', help='Model supports alerts')
    parser.add_argument('--json', action='store_true', help='Output in JSON format for programmatic use')
    parser.add_argument('--verbose', action='store_true', help='Show detailed human-readable output (default without --json)')
    
    args = parser.parse_args()
    
    # Note: Ben's bidding models typically use 24 cards (grouped pips)
    if 'bidding' in args.model.lower() or not any(x in args.model.lower() for x in ['play', 'lead', 'dummy', 'decl', 'lefty', 'righty']):
        if args.n_cards == 32:
            if not args.json and (args.verbose or not args.json):
                print("Note: Bidding models typically use 24 cards (grouped pips). Using n_cards=24")
            args.n_cards = 24
    
    # Determine output settings
    # Only show human output if not using JSON, or if using verbose without JSON
    show_human_output = not args.json and (args.verbose or True)
    
    # Create inference object
    try:
        inference = BiddingInference(
            model_path=args.model,
            n_cards=args.n_cards,
            model_version=args.model_version,
            alert_supported=args.alert_supported,
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
        result = inference.predict_bid(
            hand_str=args.hand,
            auction=args.auction,
            vuln=args.vuln,
            dealer=args.dealer,
            seat=args.seat
        )
        
        if args.json:
            # Structured JSON output
            json_output = {
                "success": True,
                "input": {
                    "hand": args.hand,
                    "auction": args.auction if args.auction else None,
                    "vulnerability": args.vuln,
                    "dealer": args.dealer,
                    "seat": args.seat,
                    "model": os.path.basename(args.model)
                },
                "result": {
                    "recommended_bid": result['top_bid'],
                    "confidence": round(result['top_bid_prob'], 4),
                    "bids": [
                        {
                            "bid": bid_info['bid'],
                            "probability": round(bid_info['probability'], 4)  # 4 decimal places = 0.01% precision
                        }
                        for bid_info in result['top_bids']
                    ],
                    "all_bids": {
                        bidding.ID2BID[i]: float(result.get('all_probs', result.get('current_probs', []))[i] 
                                           if i < len(result.get('all_probs', result.get('current_probs', []))) else 0.0)
                        for i in range(40)
                    } if args.verbose else None,
                    "metrics": {
                        "entropy": round(result['entropy'], 4),
                        "max_probability": round(result['max_prob'], 4),
                        "top5_total_probability": round(result['total_top_5_prob'], 4),
                        "inference_time_seconds": round(result['inference_time'], 3)  # millisecond precision
                    }
                }
            }
            
            if 'alert_probability' in result:
                json_output['result']['alert_probability'] = round(result['alert_probability'], 4)
            
            # Remove None values for cleaner output
            if not args.verbose:
                json_output['result'].pop('all_bids', None)
            
            print(json.dumps(json_output, indent=2))
        
        if show_human_output:
            # Human-readable output
            print(f"\nHand: {args.hand}")
            print(f"Auction: {args.auction if args.auction else '(opening bid)'}")
            print(f"Vulnerability: {args.vuln}")
            print(f"Dealer: {args.dealer}")
            print(f"Seat: {args.seat}")
            print(f"\n{'='*50}")
            print(f"Recommended bid: {result['top_bid']} ({result['top_bid_prob']:.1%})")
            print(f"\nTop 5 bid options:")
            for i, bid_info in enumerate(result['top_bids'], 1):
                print(f"  {i}. {bid_info['bid']:5s} - {bid_info['probability']:.1%}")
            
            if args.verbose:
                # Show confidence analysis
                print(f"\nConfidence Analysis:")
                print(f"  Max probability: {result['max_prob']:.1%}")
                print(f"  Top 5 total: {result['total_top_5_prob']:.1%}")
                print(f"  Entropy: {result['entropy']:.2f} (lower = more confident)")
                print(f"  Inference time: {result['inference_time']:.3f} seconds")
            
            if 'alert_probability' in result:
                print(f"\nAlert probability: {result['alert_probability']:.1%}")
            
    except Exception as e:
        if args.json:
            error_output = {
                "error": str(e),
                "success": False,
                "input": {
                    "hand": args.hand,
                    "auction": args.auction if args.auction else None,
                    "vulnerability": args.vuln,
                    "dealer": args.dealer,
                    "seat": args.seat,
                    "model": os.path.basename(args.model)
                }
            }
            print(json.dumps(error_output, indent=2))
        else:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()