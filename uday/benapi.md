# Ben Bridge API Documentation

**API Base URL**: `http://142.93.198.48:8085`

## Overview

This Ben Bridge API provides AI-powered bridge analysis including bidding recommendations, opening leads, and card play suggestions. The API uses the GIB-BBO neural network models and is completely stateless - each request must include full game context.

## Available Endpoints

### 1. `/bid` - Bidding Recommendations
### 2. `/lead` - Opening Lead Analysis  
### 3. `/play` - Card Play Decisions
### 4. `/claim` - Claim Evaluation

---

## `/bid` - Bidding Recommendations

Get AI bidding suggestions for any auction situation.

### Required Parameters
- `hand`: Player's hand in PBN format (e.g., "AKQ.JT9.8765.432")
- `dealer`: Dealer position (N/E/S/W)
- `seat`: Player's seat (N/E/S/W)

### Optional Parameters
- `ctx`: Auction context (empty for opening bid, see format below)
- `vul`: Vulnerability (`""=None`, `@v=NS`, `@V=EW`, `@v@V=Both`)
- `user`: User identifier for tracking

### Examples

**Opening Bid**:
```bash
curl "http://142.93.198.48:8085/bid?hand=AKQ.JT9.8765.432&dealer=N&seat=N&vul=&ctx=&user=test"
```
Response: `{"bid": "1NT", "who": "NN", "quality": "0.95"}`

**Response to 1♣**:
```bash
curl "http://142.93.198.48:8085/bid?hand=J87.AK5.QT63.A42&dealer=N&seat=S&vul=&ctx=1C--&user=test"
```
Response: `{"bid": "1D", "who": "NN", "quality": "0.87"}`

**Competitive Bidding**:
```bash
curl "http://142.93.198.48:8085/bid?hand=KQ987.A6.752.K43&dealer=N&seat=W&vul=EW&ctx=1C1S&user=test"
```

**Complex Auction**:
```bash
curl "http://142.93.198.48:8085/bid?hand=A87.KQ5.QT63.A42&dealer=N&seat=S&vul=@v@V&ctx=1C--1H--1S--2H--&user=test"
```

### Auction Format (`ctx` parameter)

Bids are encoded as 2-character strings:
- **Suits**: `1C`, `1D`, `1H`, `1S` (clubs, diamonds, hearts, spades)  
- **NT**: `1N`, `2N`, `3N` (not 1NT!)
- **Pass**: `--`
- **Double**: `Db`  
- **Redouble**: `Rd`

**Example Auctions**:
- Opening bid: `ctx=`
- 1♣-Pass-1♥-Pass: `ctx=1C--1H--`
- 1♣-1♠-Double: `ctx=1C1SDb`
- 1NT-Pass-3NT: `ctx=1N--3N`

---

## `/lead` - Opening Lead Analysis

Get AI recommendations for opening leads after the auction is complete.

### Required Parameters
- `hand`: Leader's hand in PBN format
- `dealer`: Dealer position (N/E/S/W)
- `seat`: Leader's seat (N/E/S/W) 
- `ctx`: Complete auction ending in final contract

### Optional Parameters
- `vul`: Vulnerability
- `user`: User identifier

### Examples

**Leading Against 3NT**:
```bash
curl "http://142.93.198.48:8085/lead?hand=KJ97.Q85.T63.A42&dealer=N&seat=W&vul=&ctx=1N--3N&user=test"
```

**Leading Against 4♠**:
```bash
curl "http://142.93.198.48:8085/lead?hand=A73.KQ85.964.T32&dealer=N&seat=W&vul=&ctx=1S--4S--&user=test"
```

**Leading Against Slam**:
```bash
curl "http://142.93.198.48:8085/lead?hand=876.QJ95.T832.Q4&dealer=N&seat=W&vul=&ctx=1C--1H--1S--3N--6N&user=test"
```

**Leading Against Doubled Contract**:
```bash
curl "http://142.93.198.48:8085/lead?hand=KQJ9.A8.T654.J32&dealer=N&seat=W&vul=@v&ctx=1S2HDbRd3S--&user=test"
```

### Response Format
```json
{
  "card": "S4",
  "who": "NN - best",
  "quality": "Good",
  "candidates": [
    {"card": "S4", "insta_score": 0.45, "expected_tricks_sd": 3.2},
    {"card": "H3", "insta_score": 0.30, "expected_tricks_sd": 3.5}
  ]
}
```

---

## `/play` - Card Play Analysis

Get AI recommendations for card play during the hand.

### Required Parameters
- `hand`: Player's current hand in PBN format
- `dummy`: Dummy's hand in PBN format (if visible)
- `dealer`: Dealer position (N/E/S/W)
- `seat`: Player's seat (N/E/S/W)
- `ctx`: Auction (to determine contract and declarer)

### Optional Parameters
- `played`: Cards already played (e.g., "CKCAC2C3STSJSQSA")
- `vul`: Vulnerability
- `user`: User identifier

### Examples

**Declarer Play at Trick 1**:
```bash
curl "http://142.93.198.48:8085/play?hand=AQ6.K74.AK53.A82&dummy=K73.AQ6.QJ82.QJ4&dealer=S&seat=S&vul=&ctx=1N--3N&played=S5S3SJ&user=test"
```

**Third Hand Play**:
```bash
curl "http://142.93.198.48:8085/play?hand=AJ9.8752.T94.K65&dummy=K73.AQ6.QJ82.QJ4&dealer=S&seat=E&vul=&ctx=1N--3N&played=S5S3&user=test"
```

**Dummy Play**:
```bash
curl "http://142.93.198.48:8085/play?hand=K73.AQ6.QJ82.QJ4&dummy=AQ6.K74.AK53.A82&dealer=S&seat=N&vul=&ctx=1N--3N&played=S5&user=test"
```

**Later in the Hand**:
```bash
curl "http://142.93.198.48:8085/play?hand=A6.K7.AK5.A&dummy=K7.AQ.QJ8.Q&dealer=S&seat=S&vul=&ctx=1N--3N&played=S5S3SJSQS2S7S9SKHKHQH2H3&user=test"
```

### Cards Played Format

Cards are encoded as 2-character strings (Suit+Rank):
- **Suits**: S=♠, H=♥, D=♦, C=♣
- **Ranks**: A,K,Q,J,T(10),9,8,7,6,5,4,3,2
- **Examples**: SA=♠A, HT=♥10, D7=♦7, CK=♣K

Cards are listed in play order: "S5S3SJSQ" = ♠5-♠3-♠J-♠Q (one trick)

---

## Hand Format (PBN)

All hands use **Portable Bridge Notation** format:
```
"Spades.Hearts.Diamonds.Clubs"
```

### Examples:
- `"AKQ7.J85.964.T32"` = ♠AKQ7 ♥J85 ♦964 ♣T32
- `"AKQJT98.-.AK.A"` = ♠AKQJT98 ♥- ♦AK ♣A (void hearts)
- `"-.AKQJT9876.-.AK"` = ♠- ♥AKQJT9876 ♦- ♣AK (red two-suiter)

**Important**: Use dots (.) to separate suits, or underscores (_) in URLs.

---

## Vulnerability Encoding

- **None**: `vul=` or `vul=None`
- **NS Vulnerable**: `vul=@v` 
- **EW Vulnerable**: `vul=@V`
- **Both Vulnerable**: `vul=@v@V`

---

## Response Formats

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
  "who": "NN - best",
  "quality": "Good", 
  "candidates": [
    {"card": "S4", "insta_score": 0.45, "expected_tricks_sd": 3.2},
    {"card": "H3", "insta_score": 0.30, "expected_tricks_sd": 3.5}
  ]
}
```

### Card Play Response
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

---

## Advanced Usage

### Detailed Analysis
Add `&details=true` for additional analysis:
```bash
curl "http://142.93.198.48:8085/bid?hand=AKQ.JT9.8765.432&dealer=N&seat=N&vul=&ctx=&user=test&details=true"
```

### Matchpoint vs IMPs
Add `&tournament=mp` for matchpoint scoring:
```bash
curl "http://142.93.198.48:8085/lead?hand=KJ97.Q85.T63.A42&dealer=N&seat=W&vul=&ctx=1N--3N&tournament=mp&user=test"
```

---

## Programming Examples

### Python
```python
import requests
import json

API_BASE = "http://142.93.198.48:8085"

def get_bid(hand, dealer="N", seat="N", auction="", vulnerability=""):
    url = f"{API_BASE}/bid"
    params = {
        "hand": hand,
        "dealer": dealer,
        "seat": seat,
        "ctx": auction,
        "vul": vulnerability,
        "user": "python_client"
    }
    response = requests.get(url, params=params)
    return response.json()

# Example usage
result = get_bid("AKQ.JT9.8765.432")
print(f"Recommended bid: {result['bid']}")

result = get_bid("J87.AK5.QT63.A42", seat="S", auction="1C--")
print(f"Response to 1♣: {result['bid']}")
```

### JavaScript
```javascript
const API_BASE = "http://142.93.198.48:8085";

async function getBid(hand, dealer="N", seat="N", auction="", vulnerability="") {
    const url = new URL(`${API_BASE}/bid`);
    url.searchParams.append("hand", hand);
    url.searchParams.append("dealer", dealer);
    url.searchParams.append("seat", seat);
    url.searchParams.append("ctx", auction);
    url.searchParams.append("vul", vulnerability);
    url.searchParams.append("user", "js_client");
    
    const response = await fetch(url);
    return await response.json();
}

// Example usage
getBid("AKQ.JT9.8765.432").then(result => {
    console.log(`Recommended bid: ${result.bid}`);
});
```

### cURL Script
```bash
#!/bin/bash
API="http://142.93.198.48:8085"

# Function to get bidding recommendation
get_bid() {
    local hand=$1
    local dealer=${2:-N}
    local seat=${3:-N}  
    local auction=${4:-}
    local vuln=${5:-}
    
    curl -s "$API/bid?hand=$hand&dealer=$dealer&seat=$seat&ctx=$auction&vul=$vuln&user=script"
}

# Examples
get_bid "AKQ.JT9.8765.432"
get_bid "J87.AK5.QT63.A42" "N" "S" "1C--"
```

---

## Performance Notes

- **Bidding**: Fast (100-200ms) - pure neural network inference
- **Opening Leads**: Slower (1-2 seconds) - uses sampling and evaluation
- **Card Play**: Medium (500ms-1s) - depends on position and complexity
- **Rate Limits**: 100/minute, 5000/hour, 20000/day per IP

---

## Troubleshooting

### Common Errors

**"Dealer, auction, and seat do not match"**
```
Error: Bidding sequence doesn't match dealer/seat positions
Fix: Ensure auction length corresponds to correct player's turn
```

**"Hand and dummy are identical"**  
```
Error: Same hand passed for both parameters
Fix: Verify hand and dummy strings are different
```

**"Invalid hand format"**
```
Error: Hand not in proper PBN format
Fix: Use format "S.H.D.C" with exactly 13 cards total
```

### Debugging Tips

1. **Validate Hand Format**: Must be 16 chars with 3 dots (e.g., "AKQ7.J85.964.T32")
2. **Check Auction**: Use 2-char bid codes, ensure sequence is legal
3. **Verify Positions**: Dealer and seat must be N/E/S/W
4. **URL Encoding**: Spaces and special chars in URLs may need encoding

### Test Commands

```bash
# Test API connectivity
curl "http://142.93.198.48:8085/"

# Test simple bid
curl "http://142.93.198.48:8085/bid?hand=AKQ.JT9.8765.432&dealer=N&seat=N&vul=&ctx=&user=test"

# Test with JSON formatting
curl "http://142.93.198.48:8085/bid?hand=AKQ.JT9.8765.432&dealer=N&seat=N&vul=&ctx=&user=test" | jq '.'
```

---

## Contact & Support

- **API Status**: Check http://142.93.198.48:8085/ for uptime
- **Model**: GIB-BBO (Bridge Base Online system)
- **Version**: Ben 0.8.7.2
- **Logs**: Server-side logging enabled for debugging

This API provides professional-grade bridge analysis suitable for training, analysis, and integration into bridge applications.