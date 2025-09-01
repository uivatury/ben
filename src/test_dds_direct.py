#!/usr/bin/env python3
"""
Simple test program to directly call DDS with a mid-trick claim scenario.
Reproduces the exact DDS call from the successful claim test.
"""

import sys
sys.path.append('/home/ben/ben/src')

from ddsolver.ddsolver import DDSolver
import deck52

def card_to_code(card_str):
    """
    Convert card string like 'CQ' to deck52 code (0-51).
    
    Examples:
        'SA' -> 12 (Ace of Spades)
        'CQ' -> 41 (Queen of Clubs)
        'C9' -> 44 (Nine of Clubs)
        'CJ' -> 42 (Jack of Clubs)
    """
    return deck52.encode_card(card_str)

def code_to_card(code):
    """
    Convert deck52 code (0-51) to card string.
    
    Examples:
        41 -> 'CQ' (Queen of Clubs)
        44 -> 'C9' (Nine of Clubs)
    """
    return deck52.decode_card(code)

def test_mid_trick_claim():
    """
    Test DDS with the exact mid-trick claim scenario from the debug logs.
    
    Scenario:
    - Contract: 4H by North
    - Trump: Hearts (strain_i=2)
    - Current trick: C9 (West), CQ (North), CJ (East)
    - South to play next (leader_i=2)
    - Remaining hands as shown in PBN
    """
    
    print("=" * 60)
    print("DDS Mid-Trick Claim Test")
    print("=" * 60)
    
    # Initialize DDS solver
    print("\nInitializing DDS solver with mode=1 (always find score, reuse transport tables)")
    dd = DDSolver(dds_mode=1, verbose=True)
    
    # Setup parameters from the successful claim
    strain_i = 2  # Hearts trump
    leader_i = 2  # South to play next
    
    # Current trick cards
    current_trick_cards = ['C9', 'CQ', 'CJ']
    current_trick = [card_to_code(card) for card in current_trick_cards]
    
    # Hands in PBN format (N: followed by North East South West hands)
    hands_pbn = ['N:.KQ..Q ..5.J6 ..Q84. ..7.98']
    
    # Print the setup
    strain_names = ['NoTrump', 'Spades', 'Hearts', 'Diamonds', 'Clubs']
    position_names = ['North', 'East', 'South', 'West']
    
    print(f"\nDDS Parameters:")
    print(f"  Strain: {strain_i} ({strain_names[strain_i]})")
    print(f"  Leader: {leader_i} ({position_names[leader_i]})")
    print(f"  Current trick codes: {current_trick}")
    print(f"  Current trick cards: {current_trick_cards}")
    print(f"  Hands PBN: {hands_pbn[0]}")
    
    # Decode the hands for clarity
    print(f"\nHands breakdown:")
    hands_str = hands_pbn[0].split(':')[1]  # Remove 'N:' prefix
    hands_list = hands_str.split(' ')
    for i, hand in enumerate(hands_list):
        suits = hand.split('.')
        print(f"  {position_names[i]:5}: Spades={suits[0] or '-':3} Hearts={suits[1] or '-':3} Diamonds={suits[2] or '-':3} Clubs={suits[3] or '-':3}")
    
    # Call DDS
    print(f"\nCalling DDS.solve()...")
    print(f"  dd.solve(strain_i={strain_i}, leader_i={leader_i}, current_trick={current_trick}, hands_pbn={hands_pbn}, solutions=1)")
    
    result = dd.solve(strain_i, leader_i, current_trick, hands_pbn, 1)
    
    # Print results
    print(f"\n" + "=" * 60)
    print(f"DDS RESULT: {result}")
    print("=" * 60)
    
    if result:
        if 'max' in result and 'min' in result:
            print(f"\nInterpretation:")
            print(f"  Maximum tricks South (leader) can take: {result['max'][0]}")
            print(f"  Minimum tricks South (leader) can take: {result['min'][0]}")
            print(f"\nFor the claim: South claimed 3 more tricks (10 total with 7 already won)")
            print(f"DDS confirms: South CAN take {result['max'][0]} more tricks")
            if result['max'][0] >= 3:
                print("  ✓ CLAIM SHOULD BE ACCEPTED")
            else:
                print("  ✗ CLAIM SHOULD BE REJECTED")
        else:
            print("\nNote: Result format unexpected:", result)
    else:
        print("\n✗ DDS returned None - solver failed")
    
    print("\n" + "=" * 60)
    
    # Demonstrate card mapping functions
    print("\nCard Mapping Examples:")
    test_cards = ['SA', 'HK', 'DQ', 'CJ', 'C9', 'CQ']
    for card in test_cards:
        code = card_to_code(card)
        back = code_to_card(code)
        print(f"  '{card}' -> {code:2d} -> '{back}'")

if __name__ == "__main__":
    test_mid_trick_claim()