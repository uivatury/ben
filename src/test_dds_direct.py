#!/usr/bin/env python3

import sys
sys.path.append('/home/ben/ben/src')

from ddsolver.ddsolver import DDSolver
import json

def test_dds_direct():
    """Test DDS directly with the problematic hand"""
    
    # Initialize DDS solver
    dd = DDSolver(verbose=True)
    
    # The hand that's causing problems
    hand_pbn = "N:6...AQ32 .K8..987 QJT3...T .T9..KJ6"
    
    print("Testing DDS directly with problematic hand:")
    print(f"Hand: {hand_pbn}")
    print("\nHand breakdown:")
    print("  North: ♠6 ♥void ♦void ♣AQ32")
    print("  East:  ♠void ♥K8 ♦void ♣987")
    print("  South: ♠QJT3 ♥void ♦void ♣T")
    print("  West:  ♠void ♥T9 ♦void ♣KJ6")
    
    print("\nExpected: South can take 5 tricks (4 spades + 1 club via dummy's ace)")
    
    # Test parameters from the failing case
    strain_i = 1  # Spades trump
    player_i = 3  # South to play
    leader_i = 3  # South leads
    current_trick = []  # No current trick
    solutions = 1  # Find max tricks
    
    print(f"\nCalling DDS with:")
    print(f"  strain_i={strain_i} (Spades trump)")
    print(f"  leader_i={leader_i} (South leads)")
    print(f"  player_i={player_i} (South to play)")
    print(f"  current_trick={current_trick}")
    print(f"  solutions={solutions}")
    
    try:
        # Let's examine what DDS actually receives
        print(f"\n=== DDS Internal Parameters ===")
        
        # Show how strain_i is converted to DDS trump
        dds_trump = (strain_i - 1) % 5
        trump_names = ['Spades', 'Hearts', 'Diamonds', 'Clubs', 'NoTrump']
        print(f"strain_i={strain_i} -> DDS trump={dds_trump} ({trump_names[dds_trump]})")
        
        # Test with solutions=3 to get more detailed output
        print(f"\nTesting with solutions=3 for detailed card analysis...")
        dd_results_detailed = dd.solve(strain_i, leader_i, current_trick, [hand_pbn], 3)
        print(f"Detailed DDS Results: {dd_results_detailed}")
        
        # Now test with the original parameters
        print(f"\nTesting with solutions=1 (original)...")
        dd_results = dd.solve(strain_i, leader_i, current_trick, [hand_pbn], solutions)
        
        print(f"\nDDS Results: {dd_results}")
        
        if dd_results:
            max_tricks = dd_results.get('max', [0])[0] if 'max' in dd_results else 0
            min_tricks = dd_results.get('min', [0])[0] if 'min' in dd_results else 0
            print(f"Max tricks: {max_tricks}")
            print(f"Min tricks: {min_tricks}")
            
            if max_tricks == 0:
                print("\n🚨 BUG CONFIRMED: DDS returns 0 tricks when South should get 5!")
                
                # Let's try different player positions to see if that's the issue
                print("\n=== Testing different player positions ===")
                for test_player in range(4):
                    test_results = dd.solve(strain_i, test_player, current_trick, [hand_pbn], 1)
                    max_test = test_results.get('max', [0])[0] if test_results else 0
                    position_names = ['North', 'East', 'South', 'West']
                    print(f"Player {test_player} ({position_names[test_player]}): {max_test} tricks")
                    
            else:
                print(f"\n✅ DDS correctly returned {max_tricks} tricks")
        else:
            print("\n❌ DDS returned None (failed)")
            
    except Exception as e:
        print(f"\n❌ DDS call failed with exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_dds_direct()