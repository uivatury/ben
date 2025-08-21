# Ben API Examples and Documentation

## API Base URL
Replace `YOUR_API_IP` with your actual server IP (e.g., `142.93.198.48`)

## API Endpoints

### 1. `/bid` - Get bidding recommendations
### 2. `/lead` - Get opening lead recommendations  
### 3. `/play` - Get card play recommendations
### 4. `/claim` - Evaluate claim (if supported)

## Parameter Reference

### Common Parameters
- **`hand`**: Player's hand in PBN format (e.g., "AKQ.JT9.8765.432")
  - Format: `Spades.Hearts.Diamonds.Clubs`
  - Use dots (.) to separate suits
  - Can use underscores instead of dots in URL

- **`dealer`**: Dealer position - N, E, S, or W

- **`seat`**: Player's seat position - N, E, S, or W

- **`vul`**: Vulnerability
  - Empty or blank = None vulnerable
  - `@v` = NS vulnerable  
  - `@V` = EW vulnerable
  - `@v@V` = Both vulnerable

- **`user`**: Identifier for tracking (any string)

### Bidding-Specific Parameters
- **`ctx`**: Bidding context/auction (every 2 chars = one bid)
  - Empty = opening bid
  - `--` = PASS
  - `Db` = Double
  - `Rd` = Redouble
  - Examples: `1C--1H--` = "1♣-Pass-1♥-Pass"

### Play-Specific Parameters
- **`dummy`**: Dummy's hand in PBN format
- **`played`**: Cards already played (2 chars per card, e.g., "CKCAC2C3")
- **`tournament`**: "mp" for matchpoint, otherwise IMPs

## Examples from Your MacBook

### 1. Opening Bid
**Scenario**: You hold a balanced 15 HCP hand, no previous bids
```bash
curl "http://142.93.198.48:8085/bid?hand=AQ7.KJ8.QT65.A32&dealer=N&seat=N&vul=&ctx=&user=uday"
```
Expected: 1NT or 1D depending on system

### 2. Responding to Partner's Bid with Interference
**Scenario**: Partner opened 1♥, RHO doubled, you have support
```bash
curl "http://YOUR_API_IP:8085/bid?hand=K873.Q952.J6.K42&dealer=N&seat=S&vul=&ctx=1HDb&user=uday"
```
Expected: 2H, 3H, or XX depending on strength

**Another example**: Partner opened 1♣, RHO bid 1♠
```bash
curl "http://142.93.198.48:8085/bid?hand=J87.AK5.QT63.542&dealer=N&seat=S&vul=&ctx=1C1S&user=uday"
```
Expected: X (negative double) or 1NT

### 3. Opening Lead
**Scenario**: Leading against 3NT after 1NT-3NT auction
```bash
curl "http://142.93.198.48:8085/lead?hand=KJ97.Q85.T63.A42&dealer=S&seat=W&vul=&ctx=1N--3N&user=uday"
```
Expected: Small spade (4th best from longest suit)

**Against suit contract**: Leading against 4♠
```bash
curl "http://142.93.198.48:8085/lead?hand=A73.KQ85.964.T32&dealer=S&seat=W&vul=&ctx=1S--4S--&user=uday"
```
Expected: HK or HA (top of sequence)

### 4. Play from Dummy at Trick 1
**Scenario**: You're dummy, partner (South) led ♣K against 3NT
```bash
curl "http://142.93.198.48:8085/play?hand=876.AKQ.J32.QJT9&dummy=AKQ.JT9.8765.432&dealer=W&seat=N&vul=&ctx=1N--3N&played=CK&user=uday"
```
Note: Dummy position is relative to declarer

### 5. Play by Third Hand at Trick 1
**Scenario**: Partner led ♠5, dummy played ♠3, you're East defending 3NT
```bash
curl "http://142.93.198.48:8085/play?hand=AJ9.8752.T94.K65&dummy=K73.AQ6.QJ82.QJ4&dealer=S&seat=E&vul=&ctx=1N--3N&played=S5S3&user=uday"
```
Expected: SA or SJ (third hand high)

### 6. Play by Declarer at Trick 1
**Scenario**: West led ♠5, dummy has ♠K73, you (South) are declarer in 3NT
```bash
curl "http://142.93.198.48:8085/play?hand=AQ6.K74.AK53.A82&dummy=K73.AQ6.QJ82.QJ4&dealer=S&seat=S&vul=&ctx=1N--3N&played=S5S3SJ&user=uday"
```
Expected: SQ (cover the jack) or SA

### 7. Play at Trick 2 (Winner of Trick 1 Leads)
**Scenario**: Declarer won trick 1 with ♠A, now leading to trick 2
```bash
curl "http://142.93.198.48:8085/play?hand=A6.K74.AK53.A82&dummy=K73.AQ6.QJ82.QJ4&dealer=S&seat=S&vul=&ctx=1N--3N&played=S5S3SJSA&user=uday"
```
Note: After winning SA, declarer's hand no longer has SA

**Complex example**: After first full trick, East leads to trick 2
```bash
curl "http://142.93.198.48:8085/play?hand=J9.8752.T94.K65&dummy=K73.AQ6.QJ82.QJ4&dealer=S&seat=E&vul=&ctx=1N--3N&played=S5S3SJSQD2D8D9&user=uday"
```
Cards played: S5-S3-SJ-SQ (trick 1), D2-D8-D9 (partial trick 2)

### 8. Claim Evaluation
**Scenario**: Check if claiming 9 tricks is valid in 3NT with remaining cards
```bash
curl "http://142.93.198.48:8085/claim?hand=A.K7.AK5.A&dummy=K7.AQ.QJ8.Q&dealer=S&seat=S&vul=&ctx=1N--3N&played=S5S3SJSQS2S7S9SKHKHQH2H3&tricks=9&user=uday"
```
Note: Claim evaluation may not be fully supported in the API version

## Response Format

### Bidding Response
```json
{
  "bid": "1NT",
  "who": "NN",
  "quality": "0.95",
  "candidates": [
    {"call": "1NT", "insta_score": 0.85},
    {"call": "1D", "insta_score": 0.10}
  ],
  "hcp": [9.2, 7.3, 6.5],
  "shape": [3.2, 4.0, 3.7, 3.1]
}
```

### Opening Lead Response
```json
{
  "card": "S4",
  "who": "Simulation (MP)",
  "quality": "Good",
  "candidates": [
    {"card": "S4", "insta_score": 0.45, "expected_tricks_sd": 3.2},
    {"card": "H3", "insta_score": 0.30, "expected_tricks_sd": 3.5}
  ]
}
```

### Play Response
```json
{
  "card": "SA",
  "who": "NN - best",
  "quality": "0.92",
  "candidates": [
    {"card": "SA", "insta_score": 0.92},
    {"card": "SQ", "insta_score": 0.08}
  ]
}
```

## Card Notation
- **Suits**: S=Spades, H=Hearts, D=Diamonds, C=Clubs
- **Ranks**: A, K, Q, J, T (10), 9, 8, 7, 6, 5, 4, 3, 2
- **Cards**: Two characters - Suit+Rank (e.g., "SA" = Ace of Spades)

## Auction Format (ctx parameter)
Bids are encoded as 2-character strings concatenated:
- `1C` = 1♣
- `1N` = 1NT (N not NT)
- `--` = Pass
- `Db` = Double
- `Rd` = Redouble

Example auction "1♣-Pass-1♥-Double-2♥-Pass-Pass-Pass":
```
ctx=1C--1HDb2H------
```

## Vulnerability Encoding
- None vulnerable: `vul=`
- NS vulnerable: `vul=@v`
- EW vulnerable: `vul=@V`  
- Both vulnerable: `vul=@v@V`

## Tips for Testing

### Quick Test Script
Save this as `test_api.sh`:
```bash
#!/bin/bash
API="http://142.93.198.48:8085"

echo "Testing opening bid..."
curl "$API/bid?hand=AKQ.JT9.8765.432&dealer=N&seat=N&vul=&ctx=&user=test"
echo -e "\n"

echo "Testing response with interference..."
curl "$API/bid?hand=J87.AK5.QT63.542&dealer=N&seat=S&vul=&ctx=1C1S&user=test"
echo -e "\n"

echo "Testing opening lead..."
curl "$API/lead?hand=KJ97.Q85.T63.A42&dealer=N&seat=W&vul=&ctx=1N--3N&user=test"
echo -e "\n"

echo "Testing card play..."
curl "$API/play?hand=AQ6.K74.AK53.A82&dummy=K73.AQ6.QJ82.QJ4&dealer=S&seat=S&vul=&ctx=1N--3N&played=S5S3SJ&user=test"
```

### JSON Pretty Print
Use `jq` for formatted output:
```bash
curl "http://142.93.198.48:8085/bid?hand=AKQ.JT9.8765.432&dealer=N&seat=N&vul=&ctx=&user=test" | jq '.'
```

## Common Issues and Solutions

### Issue: "Dealer, auction, and seat do not match"
**Solution**: Ensure the auction length and dealer/seat positions are consistent. The number of bids determines whose turn it is.

### Issue: "Hand and dummy are identical"  
**Solution**: Check that you're passing different hands for `hand` and `dummy` parameters.

### Issue: Empty or unexpected responses
**Solution**: Check that:
- Hand format is correct (16 characters including 3 dots)
- Auction format uses 2-character bid codes
- Seat and dealer are valid (N, E, S, W)

## Performance Notes

- **Bidding**: Fast (~100-200ms) - uses neural network with limited sampling
- **Opening Lead**: Slower (~1-2s) - uses double dummy analysis with sampling
- **Card Play**: Medium (~500ms-1s) - depends on position and trick number
- **Claim**: Fast if supported - evaluates remaining tricks

## Advanced Options

### Add Details to Response
Add `&details=true` to get more analysis:
```bash
curl "http://142.93.198.48:8085/bid?hand=AKQ.JT9.8765.432&dealer=N&seat=N&vul=&ctx=&user=test&details=true"
```

### Matchpoint vs IMPs
Add `&tournament=mp` for matchpoint scoring:
```bash
curl "http://142.93.198.48:8085/lead?hand=KJ97.Q85.T63.A42&dealer=N&seat=W&vul=&ctx=1N--3N&tournament=mp&user=test"
```

## Testing Different Positions

Remember that play API requires careful position management:
- **Declarer**: Usually South in examples (seat=S)
- **Dummy**: Partner of declarer (seat=N if declarer is S)
- **LHO** (Left Hand Opponent): West if declarer is South (seat=W)
- **RHO** (Right Hand Opponent): East if declarer is South (seat=E)

The API automatically determines if you're declaring or defending based on the auction and your seat.
