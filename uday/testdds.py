#!/usr/bin/env python3
"""
Test DDS (Double Dummy Solver) with specific endgame positions
to diagnose claim evaluation issues.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ddsolver import ddsolver

def test_position(test_name, pbn_string, trump, leader, expected_tricks):
    """Test a single position with DDS"""
    print(f"\n{'='*60}")
    print(f"TEST: {test_name}")
    print(f"{'='*60}")
    print(f"PBN: {pbn_string}")
    print(f"Trump: {trump} (0=NT, 1=S, 2=H, 3=D, 4=C)")
    print(f"Leader: {leader} (0=N, 1=E, 2=S, 3=W)")
    print(f"Expected tricks: {expected_tricks}")
    
    # Parse PBN to show the position clearly
    hands = pbn_string.replace("N:", "").split(" ")
    positions = ["North", "East", "South", "West"]
    suits = ["♠", "♥", "♦", "♣"]
    
    print("\nPosition:")
    for i, hand in enumerate(hands):
        suit_cards = hand.split(".")
        # Ensure we have exactly 4 suits (pad with empty if needed)
        while len(suit_cards) < 4:
            suit_cards.append("")
        hand_str = " ".join([f"{suits[j]}{cards if cards else '-'}" for j, cards in enumerate(suit_cards[:4])])
        print(f"  {positions[i]}: {hand_str}")
    
    # Initialize DDS solver with exact same config as claim.py
    dd = ddsolver.DDSolver(dds_mode=1, verbose=False)
    
    # Call DDS with solutions=1 (just get max tricks)
    # Current trick is empty []
    try:
        # Call exactly like claim.py does:
        result = dd.solve(
            trump,      # Use DDS format 
            leader,     # leader_i
            [],         # current_trick empty list
            [pbn_string],  # hands_pbn as list
            1           # solutions
        )
        
        print(f"\nDDS Result: {result}")
        
        if result and 'max' in result and result['max']:
            actual_tricks = result['max'][0]
            print(f"Actual tricks: {actual_tricks}")
            
            if actual_tricks == expected_tricks:
                print(f"✓ PASS - Got expected {expected_tricks} tricks")
            else:
                print(f"✗ FAIL - Expected {expected_tricks} tricks, got {actual_tricks}")
        else:
            print(f"✗ FAIL - DDS returned no valid result")
            
    except Exception as e:
        print(f"✗ ERROR: {e}")
    
    return

def main():
    print("DDS (Double Dummy Solver) Test Suite")
    print("Testing endgame positions for claim evaluation")
    
    # Test 1: Working case - South has HA and S4, should win both
    test_position(
        "Test 1 - Working case (2 tricks)",
        "N:..T9. .K..J 4.A.. .J..7",
        trump=2,   # Hearts
        leader=2,  # South
        expected_tricks=2
    )
    
    # Test 2: Failing case - South has D9 and CJ, should win both
    # North has DQ and DJ which are high
    test_position(
        "Test 2 - Failing case (should be 2 tricks)",
        "N:..QJ. Q7... ..9.J AT...",
        trump=2,  # Hearts
        leader=2,  # South
        expected_tricks=2
    )
    
    # Test 3: Verification case - 1 trick
    # Note: The PBN might need adjustment based on exact requirements
    test_position(
        "Test 3 - Verification case (1 trick)",
        "N:..T9. .KJ.. 4.A.. ...J7",
        trump=2,  # Hearts
        leader=2,  # South
        expected_tricks=1
    )
    
    # Additional test: Simple case with clear winners
    test_position(
        "Test 4 - Simple AK vs small (2 tricks)",
        "N:AK... 45... 23... 67...",
        trump=0,  # NoTrump
        leader=0,  # North
        expected_tricks=2
    )
    
    print("\n" + "="*60)
    print("Test suite complete")

if __name__ == "__main__":
    main()
