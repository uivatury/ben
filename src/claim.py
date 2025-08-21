import time
import deck52
import random
import numpy as np
from itertools import combinations

class Claimer:

    def __init__(self, verbose, ddsolver) -> None:
        self.verbose = verbose
        self.dd = ddsolver

    def claimcheck(self, strain_i, player_i, hands52, tricks52, claim_cards, shown_out_suits, missing_cards, current_trick, n_samples, tricks):
        # If any voids we will not manipulate the suit, as we can take finesses if needed
        # We remove any intermediate cards, so there is no finesse 
        hidden_cards = []
        used_cards =  [item for row in tricks52 for item in row] + current_trick

        for i in range(52):
            if i in used_cards:
                continue
            if i in current_trick:
                continue
            if hands52[0][i] == 1:
                continue
            if hands52[1][i] == 1:
                continue
            hidden_cards.append(i)
        used_cards.sort()
        index_for_dummy = 2
        if player_i == 0:
            index_for_dummy = 1  
        if player_i == 2:
            index_for_dummy = 3 
        n = 13 * 4  # Number of cards per hand
        hands = [np.zeros(n, dtype=np.int32) for _ in range(4)]
        for i in range(4):
            # all cards know for this suit
            if missing_cards[i] == 0:
                for j in range(13):
                    card52 = i * 13 + j
                    # Do not transfer cards if played in current trick
                    if card52 in current_trick:
                        continue
                    hands[0][card52] = hands52[0][card52] 
                    hands[index_for_dummy][card52] = hands52[1][card52] 
                continue
            # if we have a card lower than a missing card we swap it with the lovest hidden card in that suit
            hidden_for_suit = [c for c in hidden_cards if c >= i * 13 and c < (i + 1) * 13]
            #print("suit", i, hidden_for_suit)

            for j in range(13):
                card52 = i * 13 + j
                # Do not transfer cards if played in current trick
                if card52 in current_trick:
                    continue
                if hands52[0][card52] == 1:
                    # Remember 0 = Ace
                    if len(hidden_for_suit) == 0 or card52 < hidden_for_suit[0]: 
                        hands[0][card52] = 1
                    else:
                        # Never swap to a higher card
                        if hidden_for_suit[-1] < card52:
                            hands[0][card52] = 1
                            continue
                        hands[0][hidden_for_suit[-1]] = 1
                        for k in range(len(hidden_cards)):
                            if hidden_cards[k] == hidden_for_suit[-1]:
                                hidden_cards[k] = card52
                                break  # Stop after the first replacement
                        hidden_for_suit = hidden_for_suit[:-1]

                if hands52[1][card52] == 1:
                    # Remember 0 = Ace
                    if len(hidden_for_suit) == 0 or card52 < hidden_for_suit[0]: 
                        hands[index_for_dummy][card52] = 1
                    else:
                        # Never swap to a higher card
                        if hidden_for_suit[-1] < card52:
                            hands[index_for_dummy][card52] = 1
                            continue
                        hands[index_for_dummy][hidden_for_suit[-1]] = 1
                        for k in range(len(hidden_cards)):
                            if hidden_cards[k] == hidden_for_suit[-1]:
                                hidden_cards[k] = card52
                                break  # Stop after the first replacement
                        hidden_for_suit = hidden_for_suit[:-1]

        if self.verbose:
            hands_pbn = ['N:' + ' '.join([deck52.deal_to_str(hand) for hand in hands])]
            print("Claiming for player", player_i, hands_pbn)
        
        hands[0] = deck52.deal_to_str(hands[0])
        hands[index_for_dummy] = deck52.deal_to_str(hands[index_for_dummy])

        # With 6 or less cards, we should probably just check all combinations instead of shuffle
        sampled_hands_pbn = []
        # Ensure the number of combinations is correct based on the number of hidden cards
        n_cards = len(hidden_cards) // 2
        card_combinations = list(combinations(hidden_cards, n_cards))  # Get all possible splits

        # Ensure the number of requested samples doesn't exceed available combinations
        n_possible_samples = min(n_samples, len(card_combinations))

        # Select unique samples without replacement
        unique_combinations = random.sample(card_combinations, n_possible_samples)

        # We should check shown_out_suits
        #print("shown_out_suits", shown_out_suits)
        for chosen_combination  in unique_combinations:

            # Create the hands based on the selected combination
            remaining_cards = [card for card in hidden_cards if card not in chosen_combination]
            
            if index_for_dummy == 2:
                hands[3] = deck52.deal_to_str(_hand_from_cards(52, list(chosen_combination)))
                hands[1] = deck52.deal_to_str(_hand_from_cards(52, remaining_cards))
            if index_for_dummy == 1:
                hands[3] = deck52.deal_to_str(_hand_from_cards(52, list(chosen_combination)))
                hands[2] = deck52.deal_to_str(_hand_from_cards(52, remaining_cards))
            if index_for_dummy == 3:
                hands[2] = deck52.deal_to_str(_hand_from_cards(52, list(chosen_combination)))
                hands[1] = deck52.deal_to_str(_hand_from_cards(52, remaining_cards))
            sampled_hands_pbn.append('N:' + ' '.join(hands))

        #print('\n'.join(sampled_hands_pbn))
        #print("Trump",strain_i)
        dd_solved = self.dd.solve(strain_i, (4 - len(current_trick)) % 4, current_trick, sampled_hands_pbn, 3)
        # Filter keys where all values in the list are equal
        equal_value_keys = {key: values[0] for key, values in dd_solved.items() if all(value == values[0] for value in values)}

        if equal_value_keys:
            # Find the maximum value among keys with all equal values
            max_value = max(equal_value_keys.values())
            if self.verbose:
                print(f"Max value: {max_value}")
            if  max_value < tricks:
                # None of the cards give same result for all combinations
                # So we just ignore our claimcheck
                if self.verbose:
                    print(f"No cards yield the needed tricks {tricks} best {max_value}")
                bad_plays = claim_cards
            else:
                # Collect keys that:
                # - Either have all equal values but are NOT the max
                # - Or have non-uniform values
                non_max_keys = [
                    key
                    for key, values in dd_solved.items()
                    if (key in equal_value_keys and equal_value_keys[key] != max_value)
                    or (key not in equal_value_keys)
                ]
                bad_plays = [key for key in non_max_keys if key in claim_cards]
                # This should probably be extended as we might have moved a card to be a pip
                # and DDSolver is not aware of that, and only reports the first card from a sequence
                # will create redundant cards, but that is OK
                for card in claim_cards:
                    if card not in equal_value_keys:
                        bad_plays.append(card)
        else:
            # None of the cards give same result for all combinations
            # So we just ignore our claimcheck
            bad_plays = claim_cards


        if self.verbose:
            print(f"Play without sure claim: {bad_plays}")
        return bad_plays

    def claimapi(self, strain_i, player_i, hands52, n_samples, hidden_cards, current_trick, claimer_board_pos=None, decl_board_pos=None, tricks_already_won=0):
        t_start = time.time()

        # Enhanced debugging: Log input parameters
        if self.verbose:
            total_cards_in_hands = sum(np.sum(hand) for hand in hands52)
            hidden_card_count = np.sum(hidden_cards)
            current_trick_count = len(current_trick)
            print(f"CLAIM DEBUG: strain_i={strain_i}, player_i={player_i}, n_samples={n_samples}")
            print(f"CLAIM DEBUG: total_cards_in_hands={total_cards_in_hands}, hidden_cards={hidden_card_count}, current_trick_cards={current_trick_count}")
            print(f"CLAIM DEBUG: expected total = {total_cards_in_hands + hidden_card_count + current_trick_count} (should be 52)")
            # Debug the actual hands52 content
            for i, hand in enumerate(hands52):
                hand_card_count = np.sum(hand)
                print(f"CLAIM DEBUG: hands52[{i}] has {hand_card_count} cards")
                if hand_card_count > 0:
                    print(f"  Hand {i}: {deck52.deal_to_str(hand)}")

        # Setup seen and hidden hand indexes using board coordinates
        # claimer_board_pos is the board position of the claimer (NESW: 0=N, 1=E, 2=S, 3=W)
        # decl_board_pos is the board position of the declarer
        if self.verbose:
            print(f"CLAIM DEBUG: claimer_board_pos={claimer_board_pos}, decl_board_pos={decl_board_pos}")
        
        if claimer_board_pos is not None and decl_board_pos is not None:
            # Use board positions to determine seen and hidden hands
            dummy_board_pos = (decl_board_pos + 2) % 4
            
            # Determine which hands are visible (seen) to the claimer
            if claimer_board_pos == decl_board_pos:
                # Declarer is claiming, sees dummy
                seen_hand_indexes = [claimer_board_pos, dummy_board_pos]
            elif claimer_board_pos == dummy_board_pos:
                # Dummy is claiming, sees declarer
                seen_hand_indexes = [claimer_board_pos, decl_board_pos]
            else:
                # Defender is claiming, sees dummy (NOT partner!)
                # Defenders can see their own hand and dummy (which is face-up)
                seen_hand_indexes = [claimer_board_pos, dummy_board_pos]
            
            hidden_hand_indexes = [i for i in range(4) if i not in seen_hand_indexes]
        else:
            # Fallback to old logic if board positions not provided
            seen_hand_indexes = [player_i, 3 if player_i == 1 else 1]
            hidden_hand_indexes = [i for i in range(4) if i not in seen_hand_indexes]
        
        # Clean up hands52 to ensure only 0s and 1s (no negative values from partial hands)
        clean_hands52 = [np.maximum(0, hand) for hand in hands52]
        
        # Convert from CardPlayer order [lefty, dummy, righty, declarer] to NESW order [N, E, S, W]
        if decl_board_pos is not None:
            nesw_hands52 = [None] * 4
            nesw_hands52[decl_board_pos] = clean_hands52[3]  # declarer
            nesw_hands52[(decl_board_pos + 2) % 4] = clean_hands52[1]  # dummy
            nesw_hands52[(decl_board_pos + 1) % 4] = clean_hands52[0]  # lefty
            nesw_hands52[(decl_board_pos + 3) % 4] = clean_hands52[2]  # righty
        else:
            # Fallback to original order if decl_board_pos not available
            nesw_hands52 = clean_hands52
            
        hands_pbn = ['N:' + ' '.join([deck52.deal_to_str(hand) for hand in nesw_hands52])]
        if self.verbose:
            print(f"Claiming for player {player_i} {hands_pbn}")
            print(f"Current trick: {[deck52.decode_card(card) for card in current_trick]}")
            print(f"Seen hands (known): positions {seen_hand_indexes}")
            print(f"Hidden hands (unknown): positions {hidden_hand_indexes}")
            print(f"CLAIM DEBUG: Original hands array before modification: {hands_pbn[0] if hands_pbn else 'None'}")
        
        # Validate card count before proceeding
        # Note: individual hands can have negative counts with partial hands + played cards
        # The validation should focus on total deck integrity
        hidden_card_count = np.sum(hidden_cards)
        current_trick_count = len(current_trick)
        
        # For partial hands, we validate differently - check that hidden + current_trick makes sense
        expected_remaining = 52 - sum(max(0, np.sum(hand)) for hand in hands52)  # Only count positive cards
        actual_remaining = hidden_card_count + current_trick_count
        
        if self.verbose:
            total_cards_in_hands = sum(np.sum(hand) for hand in hands52)  # Can be negative with partial hands
            print(f"CLAIM DEBUG: Card validation - hands={total_cards_in_hands:.1f}, hidden={hidden_card_count:.1f}, current_trick={current_trick_count}")
            print(f"CLAIM DEBUG: Expected remaining={expected_remaining}, actual remaining={actual_remaining}")
        
        # Skip strict validation for partial hands - the card play simulation handles the complexity
        if False:  # Disable the problematic validation for now
            print(f"ERROR: Card count mismatch! Total={total_cards}, Expected=52")
            print(f"  Cards in hands: {total_cards_in_hands}")
            print(f"  Hidden cards: {hidden_card_count}")
            print(f"  Current trick: {current_trick_count}")
            return 0, n_samples  # Conservative: reject claim if card counts don't add up

        sampled_hands_pbn = []
        hidden_cards = list(np.nonzero(hidden_cards)[0])
        
        if self.verbose:
            print(f"CLAIM DEBUG: Hidden card indices: {hidden_cards}")
            print(f"CLAIM DEBUG: Hidden cards decoded: {[deck52.decode_card(c) for c in hidden_cards]}")

        if len(hidden_cards) == 0:
            if self.verbose:
                print("No hidden cards - using known hands only")
            # No sampling needed, use the known hands
            sampled_hands_pbn = hands_pbn
        else:
            # Start with the known hands in correct positions, unknown positions as None
            hands = [None, None, None, None]
            
            # Convert board positions to CardPlayer positions to access hands52
            # hands52 is in CardPlayer order: [lefty, dummy, righty, declarer]
            # Board positions: 0=N, 1=E, 2=S, 3=W
            # CardPlayer mapping: lefty=(decl+1)%4, dummy=(decl+2)%4, righty=(decl+3)%4, declarer=decl
            board_to_cardplayer = {}
            board_to_cardplayer[decl_board_pos] = 3  # declarer
            board_to_cardplayer[(decl_board_pos + 2) % 4] = 1  # dummy
            board_to_cardplayer[(decl_board_pos + 1) % 4] = 0  # lefty
            board_to_cardplayer[(decl_board_pos + 3) % 4] = 2  # righty
            
            # Clean up hands52 to ensure only 0s and 1s (no negative values from partial hands)
            # Convert board positions in seen_hand_indexes to CardPlayer positions
            cp_idx_0 = board_to_cardplayer[seen_hand_indexes[0]]
            cp_idx_1 = board_to_cardplayer[seen_hand_indexes[1]]
            clean_hand_0 = np.maximum(0, hands52[cp_idx_0].copy())
            clean_hand_1 = np.maximum(0, hands52[cp_idx_1].copy())
            
            if self.verbose:
                print(f"CLAIM DEBUG: CardPlayer mapping - seen_pos {seen_hand_indexes[0]} -> CP {cp_idx_0}, seen_pos {seen_hand_indexes[1]} -> CP {cp_idx_1}")
                print(f"CLAIM DEBUG: hands52[{cp_idx_0}] = {np.sum(hands52[cp_idx_0])} cards, hands52[{cp_idx_1}] = {np.sum(hands52[cp_idx_1])} cards")
                print(f"CLAIM DEBUG: clean_hand_0 = {np.sum(clean_hand_0)} cards, clean_hand_1 = {np.sum(clean_hand_1)} cards")
            
            # Note: We no longer add current trick cards back to hands
            # DDS handles partial tricks natively via currentTrickSuit/Rank fields
            
            hands[seen_hand_indexes[0]] = deck52.deal_to_str(clean_hand_0)
            hands[seen_hand_indexes[1]] = deck52.deal_to_str(clean_hand_1)

            for i in range(n_samples):
                np.random.shuffle(hidden_cards)
                
                n_cards = len(hidden_cards) // 2
                
                # Create hands for the hidden hand positions  
                hidden_hand_0 = _hand_from_cards(52, hidden_cards[:n_cards])
                hidden_hand_1 = _hand_from_cards(52, hidden_cards[n_cards:])
                
                # Note: We no longer add current trick cards to hidden hands
                # DDS handles partial tricks natively via currentTrickSuit/Rank fields
                
                # ONLY assign to hidden positions, keep known hands unchanged
                hands[hidden_hand_indexes[0]] = deck52.deal_to_str(hidden_hand_0)
                hands[hidden_hand_indexes[1]] = deck52.deal_to_str(hidden_hand_1)

                # hands array is already in board position order (NESW)
                if claimer_board_pos is not None and decl_board_pos is not None:
                    # hands array uses board positions: [North, East, South, West]
                    # Just copy directly - no conversion needed
                    board_hands = ['...', '...', '...', '...']
                    for i in range(4):
                        board_hands[i] = hands[i] if hands[i] else '...'
                    
                    sample_hand = 'N:' + ' '.join(board_hands)
                else:
                    # Fallback to original logic if board positions not provided
                    hands_str = [h if h is not None else '...' for h in hands]
                    sample_hand = 'N:' + ' '.join(hands_str)
                
                sampled_hands_pbn.append(sample_hand)
                if self.verbose and i == 0:  # Only print first sample
                    print(f"Sample hand generated: {sample_hand}")

        try:
            # Use board position for DDS call, not CardPlayer position
            dds_player_i = claimer_board_pos if claimer_board_pos is not None else player_i
            if self.verbose:
                print(f"CLAIM DEBUG: Using DDS player position: {dds_player_i} (board pos) instead of {player_i} (CardPlayer pos)")
            
            max_min_tricks = self._get_max_min_tricks(strain_i, dds_player_i, sampled_hands_pbn, current_trick)
            if self.verbose:
                print(f"CLAIM DEBUG: DDS returned max_min_tricks = {max_min_tricks}")
        except Exception as e:
            print(f"ERROR in _get_max_min_tricks: {e}")
            if self.verbose:
                print(f"  Failed hands: {sampled_hands_pbn}")
                print(f"  Current trick: {current_trick}")
            return 0, n_samples  # Conservative: assume no tricks can be claimed on error
        
        # Add tricks already won to get total claimable tricks
        total_claimable = tricks_already_won + max_min_tricks
        
        if self.verbose:
            print(f'player {player_i} could claim {max_min_tricks} more tricks (already won: {tricks_already_won}, total: {total_claimable}).')
            print(f'claim check took {time.time() - t_start}')

        return total_claimable, n_samples

    def claim(self, strain_i, player_i, hands52, n_samples):
        t_start = time.time()

        hands_pbn = ['N:' + ' '.join([deck52.deal_to_str(hand) for hand in hands52])]

        if self.verbose:
            print(f"Claiming for player {player_i} {hands_pbn}")
        sampled_hands_pbn = []
        seen_hand_indexes = [player_i, 3 if player_i == 1 else 1]
        hidden_hand_indexes = [i for i in range(4) if i not in seen_hand_indexes]
        hidden_cards = (
            list(np.nonzero(hands52[hidden_hand_indexes[0]])[0]) +
            list(np.nonzero(hands52[hidden_hand_indexes[1]])[0])
        )

        hands = [None, None, None, None]
        hands[seen_hand_indexes[0]] = deck52.deal_to_str(hands52[seen_hand_indexes[0]])
        hands[seen_hand_indexes[1]] = deck52.deal_to_str(hands52[seen_hand_indexes[1]])

        for i in range(n_samples):
            np.random.shuffle(hidden_cards)
            
            n_cards = len(hidden_cards) // 2
            hands[hidden_hand_indexes[0]] = deck52.deal_to_str(_hand_from_cards(52, hidden_cards[:n_cards]))
            hands[hidden_hand_indexes[1]] = deck52.deal_to_str(_hand_from_cards(52, hidden_cards[n_cards:]))

            sampled_hands_pbn.append('N:' + ' '.join(hands))

        max_min_tricks = min(
            self._get_max_min_tricks(strain_i, player_i, hands_pbn, []),
            self._get_max_min_tricks(strain_i, player_i, sampled_hands_pbn, []),
        )
        
        if self.verbose:
            print(f'player {player_i} could claim {max_min_tricks} tricks.')
            print(f'claim check took {time.time() - t_start}')

        return max_min_tricks

    def _get_max_min_tricks(self, strain_i, player_i, hands_pbn, current_trick):
        leader_i = (player_i-len(current_trick)) % 4
        if self.verbose:
            print(f"CLAIM DEBUG: Calling DDS with strain={strain_i}, player={player_i}, leader={leader_i}")
            print(f"CLAIM DEBUG: First sample hand: {hands_pbn[0] if hands_pbn else 'None'}")
            print(f"CLAIM DEBUG: Current trick: {current_trick}")
            
            # Enhanced debugging: decode the hand to verify correctness
            if hands_pbn and hands_pbn[0]:
                hand_parts = hands_pbn[0].split(' ')
                if len(hand_parts) >= 4:
                    print(f"CLAIM DEBUG: Hand breakdown:")
                    positions = ['North', 'East', 'South', 'West']
                    suits = ['♠', '♥', '♦', '♣']
                    for pos_i, hand_str in enumerate(hand_parts):
                        suit_parts = hand_str.split('.')
                        print(f"  {positions[pos_i]}: {' '.join(f'{suits[i]}{cards}' for i, cards in enumerate(suit_parts))}")
            
            # BEN's strain_i already matches DDS format: 0=NT, 1=S, 2=H, 3=D, 4=C
            trump_names = ['NoTrump', 'Spades', 'Hearts', 'Diamonds', 'Clubs']
            print(f"CLAIM DEBUG: DDS trump format: strain_i={strain_i} ({trump_names[strain_i]})")
            
        # BEN's strain_i already matches DDS format: 0=NT, 1=S, 2=H, 3=D, 4=C
        # No conversion needed
        
        if self.verbose:
            print(f"CLAIM DEBUG: About to call DDS with:")
            print(f"  strain_i: {strain_i}")
            print(f"  leader_i: {leader_i}")
            print(f"  current_trick: {current_trick}")
            print(f"  hands_pbn: {hands_pbn}")
            print(f"  solutions: 1")
            print(f"  DDS solver config: dds_mode={getattr(self.dd, 'dds_mode', 'unknown')}, verbose={getattr(self.dd, 'verbose', 'unknown')}")
            
        dd_solved = self.dd.solve(strain_i, leader_i, current_trick, hands_pbn, 1)
        
        if self.verbose:
            print(f"CLAIM DEBUG: Raw DDS solve returned: {dd_solved}")
            print(f"CLAIM DEBUG: Type of result: {type(dd_solved)}")
        
        # Critical fix: Check if DDS solver returned None (failed)
        if dd_solved is None:
            if self.verbose:
                print(f"DDS solver failed for strain={strain_i}, player={player_i}, hands={hands_pbn}, current_trick={current_trick}")
            return 0  # Conservative: assume no tricks can be claimed if solver fails
        
        if self.verbose:
            print(f"CLAIM DEBUG: DDS results: {dd_solved}")
            
        max_min_tricks = 0
        for _, dd_tricks in dd_solved.items():
            max_min_tricks = max(max_min_tricks, min(dd_tricks))
        
        return max_min_tricks


def _hand_from_cards(n, cards):
    hand = np.zeros(n, dtype=np.int32)
    hand[cards] = 1
    return hand
