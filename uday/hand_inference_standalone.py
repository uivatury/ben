#!/usr/bin/env python3
"""
Standalone Hand Inference Tool - Minimal version with embedded dependencies
"""

import sys
import os
import json
import argparse
import warnings
import numpy as np

# Suppress warnings
warnings.filterwarnings("ignore", message="A NumPy version >=1.16.5 and <1.23.0 is required")

try:
    import tensorflow as tf
    from tensorflow.keras.models import load_model
    HAS_TF = True
except ImportError:
    HAS_TF = False
    print("Warning: TensorFlow not found. Install with: pip install tensorflow>=2.12", file=sys.stderr)

# ========== EMBEDDED BIDDING MODULE ==========
BID2ID = {
    'PAD_START': 0, 'PAD_END': 1, 'PASS': 2, 'X': 3, 'XX': 4,
    '1C': 5, '1D': 6, '1H': 7, '1S': 8, '1N': 9,
    '2C': 10, '2D': 11, '2H': 12, '2S': 13, '2N': 14,
    '3C': 15, '3D': 16, '3H': 17, '3S': 18, '3N': 19,
    '4C': 20, '4D': 21, '4H': 22, '4S': 23, '4N': 24,
    '5C': 25, '5D': 26, '5H': 27, '5S': 28, '5N': 29,
    '6C': 30, '6D': 31, '6H': 32, '6S': 33, '6N': 34,
    '7C': 35, '7D': 36, '7H': 37, '7S': 38, '7N': 39
}

# ========== SIMPLIFIED BINFO MODEL ==========
class BidInfoModel:
    def __init__(self, model_path):
        if not HAS_TF:
            raise ImportError("TensorFlow required for neural network model")
        self.model = load_model(model_path, compile=False)
    
    def predict(self, x):
        input_tensor = tf.convert_to_tensor(x, dtype=tf.float16)
        out_hcp, out_shape = self.model(input_tensor, training=False)
        return out_hcp.numpy(), out_shape.numpy()

# ========== BINARY ENCODING FUNCTIONS ==========
def parse_hand_24(hand_str):
    """Parse hand string to 24-card binary representation"""
    x = np.zeros((1, 24), dtype=np.float16)
    suits = hand_str.split('.')
    assert len(suits) == 4, "Hand must have 4 suits separated by dots"
    
    card_map = {'A': 0, 'K': 1, 'Q': 2, 'J': 3, 'T': 4, '9': 5, '8': 5, '7': 5, 
                '6': 5, '5': 5, '4': 5, '3': 5, '2': 5}
    
    for suit_idx, suit in enumerate(suits):
        for card in suit:
            if card in card_map:
                card_idx = card_map[card]
                x[0, suit_idx * 6 + card_idx] = 1
    return x

def get_hcp(hand):
    """Calculate HCP from binary hand representation"""
    hcp_per_card = np.array([4, 3, 2, 1, 0, 0] * 4, dtype=np.float16)
    return np.sum(hand * hcp_per_card, axis=1)

def get_shape(hand):
    """Get shape from binary hand representation"""
    return np.sum(hand.reshape((hand.shape[0], 4, -1)), axis=2)

def get_number_of_bids(auction):
    """Count actual bids (not PAD_START/PAD_END)"""
    return sum(1 for bid in auction if bid not in ['PAD_START', 'PAD_END'])

def calculate_steps(auction):
    """Calculate number of bidding rounds"""
    bids = get_number_of_bids(auction)
    if bids == 0:
        return 1
    return 1 + bids // 4

def get_auction_binary(n_steps, auction, hand_ix, hand, vuln):
    """Create binary representation of auction for model input"""
    n_samples = 1
    n_cards = 24
    
    # Feature dimensions: vuln(2) + systems(2) + hcp(1) + shape(4) + cards(24) + 4*bids(40)
    # Total: 2 + 2 + 1 + 4 + 24 + 160 = 193
    X = np.zeros((n_samples, n_steps, 193), dtype=np.float16)
    
    # Vulnerability encoding
    vuln_us_them = np.array([vuln[hand_ix % 2], vuln[(hand_ix + 1) % 2]], dtype=np.float16)
    
    # Normalize HCP and shape
    hcp = (get_hcp(hand) - 10) / 4
    shp = (get_shape(hand) - 3.25) / 1.75
    
    # Pad auction
    auction_padded = auction + ['PAD_END'] * (4 * n_steps)
    auction_ids = np.array([BID2ID.get(bid, 1) for bid in auction_padded])
    
    for step in range(n_steps):
        # Vulnerability
        X[:, step, 0:2] = vuln_us_them
        
        # Bidding systems (default to -1 meaning unknown)
        X[:, step, 2:4] = -1
        
        # HCP and shape
        X[:, step, 4] = hcp
        X[:, step, 5:9] = shp
        
        # Hand cards
        X[:, step, 9:33] = hand
        
        # Auction history (4 bids per step)
        for bid_i in range(4):
            if step == 0 and bid_i == 0:
                continue  # Skip first position in first step
            
            bid_idx = step * 4 + bid_i - 1
            if bid_idx >= 0 and bid_idx < len(auction):
                auction_offset = (hand_ix + bid_idx) % 4
                if auction_offset == 0:  # My previous bid
                    if auction_ids[bid_idx] < 40:
                        X[:, step, 33 + auction_ids[bid_idx]] = 1
                elif auction_offset == 1:  # LHO
                    if auction_ids[bid_idx] < 40:
                        X[:, step, 73 + auction_ids[bid_idx]] = 1
                elif auction_offset == 2:  # Partner
                    if auction_ids[bid_idx] < 40:
                        X[:, step, 113 + auction_ids[bid_idx]] = 1
                elif auction_offset == 3:  # RHO
                    if auction_ids[bid_idx] < 40:
                        X[:, step, 153 + auction_ids[bid_idx]] = 1
    
    return X

# ========== MAIN FUNCTIONS ==========
SEATS = {'N': 0, 'E': 1, 'S': 2, 'W': 3}
SEAT_NAMES = {0: 'North', 1: 'East', 2: 'South', 3: 'West'}

def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Standalone hand inference using BEN models',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic 1NT-3NT auction
  python hand_inference_standalone.py "KJ5.Q987.432.J65" --auction "1NT PASS 3NT PASS PASS PASS" --seat N --dealer W
  
  # Competitive auction
  python hand_inference_standalone.py "AQ32.K5.Q987.K32" --auction "1C X 1H PASS 2H" --seat E --dealer N
  
  # With specific model
  python hand_inference_standalone.py "KJ5.Q987.432.J65" --auction "1NT PASS 3NT" --seat N --dealer W \\
    --model models/TF2models/BEN-BidInfo-8730_2025-04-18-E30.keras
        """
    )
    
    parser.add_argument('hand', help='Your hand in PBN format')
    parser.add_argument('--auction', required=True, help='Space-separated auction')
    parser.add_argument('--seat', required=True, choices=['N', 'E', 'S', 'W'], help='Your seat')
    parser.add_argument('--dealer', required=True, choices=['N', 'E', 'S', 'W'], help='Dealer')
    parser.add_argument('--vuln', choices=['None', 'NS', 'EW', 'Both'], default='None')
    parser.add_argument('--model', help='Path to binfo model (.keras file)')
    parser.add_argument('--json', action='store_true', help='JSON output')
    
    return parser.parse_args()

def normalize_auction(auction_str, dealer):
    """Normalize auction and add PAD_START"""
    bids = []
    for bid in auction_str.strip().split():
        bid = bid.upper().replace('10', 'T')
        if bid in ['P', '-']:
            bids.append('PASS')
        elif bid in ['D', 'DBL', 'DOUBLE']:
            bids.append('X')
        elif bid in ['R', 'RD', 'RDBL', 'REDOUBLE']:
            bids.append('XX')
        else:
            bids.append(bid)
    
    # Add PAD_START for dealer position
    dealer_idx = SEATS[dealer]
    return ['PAD_START'] * dealer_idx + bids

def get_relative_positions(my_seat):
    """Get positions relative to me"""
    my_idx = SEATS[my_seat]
    return {
        'LHO': SEAT_NAMES[(my_idx + 1) % 4],
        'Partner': SEAT_NAMES[(my_idx + 2) % 4],
        'RHO': SEAT_NAMES[(my_idx + 3) % 4]
    }

def infer_with_model(hand_str, auction, seat, vuln, model_path):
    """Run inference using neural network model"""
    # Load model
    model = BidInfoModel(model_path)
    
    # Parse hand
    hand = parse_hand_24(hand_str)
    
    # Prepare input
    seat_idx = SEATS[seat]
    vuln_bool = {'None': [False, False], 'NS': [True, False], 
                 'EW': [False, True], 'Both': [True, True]}[vuln]
    
    n_steps = calculate_steps(auction)
    X = get_auction_binary(n_steps, auction, seat_idx, hand, vuln_bool)
    
    # Predict
    p_hcp, p_shp = model.predict(X)
    
    # Take last step predictions
    p_hcp = p_hcp.reshape((-1, n_steps, 3))[:, -1, :]
    p_shp = p_shp.reshape((-1, n_steps, 12))[:, -1, :]
    
    # Denormalize
    actual_hcp = (4 * p_hcp + 10)[0]
    actual_shape = (1.75 * p_shp + 3.25)[0]
    
    # Build results
    positions = get_relative_positions(seat)
    results = {}
    
    # Model outputs might be in different order - need to map correctly
    # Based on the issue described, let's try swapping LHO and RHO indices
    pos_indices = {'LHO': 2, 'Partner': 1, 'RHO': 0}
    
    for pos, abs_seat in positions.items():
        i = pos_indices[pos]
        results[pos] = {
            'seat': abs_seat,
            'hcp': round(float(actual_hcp[i]), 1),
            'shape': {
                'spades': round(float(actual_shape[i*4]), 1),
                'hearts': round(float(actual_shape[i*4 + 1]), 1),
                'diamonds': round(float(actual_shape[i*4 + 2]), 1),
                'clubs': round(float(actual_shape[i*4 + 3]), 1)
            }
        }
    
    return results

def format_output(results, auction_str, seat, dealer, vuln):
    """Format human-readable output"""
    lines = ["=" * 60, "HAND INFERENCE RESULTS", "=" * 60]
    lines.append(f"Auction: {auction_str}")
    lines.append(f"Your seat: {seat} | Dealer: {dealer} | Vulnerability: {vuln}")
    lines.append("-" * 60)
    
    for pos, data in results.items():
        lines.append(f"\n{pos} ({data['seat']}):")
        lines.append(f"  Estimated HCP: {data['hcp']:.1f}")
        lines.append(f"  Expected shape:")
        for suit, symbol in [('spades', '♠'), ('hearts', '♥'), 
                            ('diamonds', '♦'), ('clubs', '♣')]:
            lines.append(f"    {symbol} {data['shape'][suit]:.1f}")
    
    return "\n".join(lines)

def main():
    args = parse_arguments()
    
    # Find model if not specified
    if not args.model:
        # Look for default model
        search_paths = [
            "models/TF2models/BEN-BidInfo-8730_2025-04-18-E30.keras",
            "models/TF2models/GIB-BBOInfo-8730_2025-04-19-E30.keras",
        ]
        for path in search_paths:
            if os.path.exists(path):
                args.model = path
                break
        
        if not args.model:
            print("Error: No binfo model found. Specify with --model", file=sys.stderr)
            sys.exit(1)
    
    if not os.path.exists(args.model):
        print(f"Error: Model file not found: {args.model}", file=sys.stderr)
        sys.exit(1)
    
    # Parse auction
    auction = normalize_auction(args.auction, args.dealer)
    
    try:
        # Run inference
        results = infer_with_model(args.hand, auction, args.seat, args.vuln, args.model)
        
        if args.json:
            output = {
                'input': {
                    'hand': args.hand,
                    'auction': args.auction,
                    'seat': args.seat,
                    'dealer': args.dealer,
                    'vulnerability': args.vuln
                },
                'predictions': results,
                'model': args.model
            }
            print(json.dumps(output, indent=2))
        else:
            print(format_output(results, args.auction, args.seat, args.dealer, args.vuln))
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if not HAS_TF:
            print("Install TensorFlow: pip install tensorflow>=2.12", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()