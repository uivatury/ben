# Hand Inference Examples & Model Guide

## Available Models

### SAYC (Standard American Yellow Card) System
- `BEN-Sayc-Info-8730_2025-04-20-E30.keras` - BEN's SAYC model
- `BlueChip-Sayc-Info-8712_2024-11-29-E25.keras` - BlueChip SAYC 
- `Robo-Sayc-Info-8730_2025-05-07-E30.keras` - Robot SAYC
- `Shark-Sayc-Info-8730_2025-04-21-E30.keras` - Shark SAYC
- `WBridge5-Sayc-Info-8730_2025-04-20-E30.keras` - WBridge5 SAYC

### 2/1 Game Force System
- `BEN-21GF-Info-8730_2025-04-18-E30.keras` - BEN's 2/1 GF
- `Lia-21GF-Info-8730_2025-04-20-E30.keras` - Lia 2/1 GF
- `QPlus-21GF-Info-8730_2025-04-21-E30.keras` - Q+ 2/1 GF

### Other Systems
- `GIB-BBOInfo-8730_2025-04-19-E30.keras` - GIB/BBO system

**Recommendation**: Start with `BEN-Sayc-Info` for SAYC or `BEN-21GF-Info` for 2/1 Game Force.

## Example Use Cases

### 1. Basic NT Contract Defense

You're North defending 3NT. You want to know what the other players likely hold.

```bash
python uday/hand_inference_standalone.py "KJ5.Q987.432.J65" \
  --auction "1NT PASS 3NT PASS PASS PASS" \
  --seat N --dealer W \
  --model models/TF2models/BEN-Sayc-Info-8730_2025-04-20-E30.keras
```

**Output**:
```
============================================================
HAND INFERENCE RESULTS
============================================================
Auction: 1NT PASS 3NT PASS PASS PASS
Your seat: N | Dealer: W | Vulnerability: None
------------------------------------------------------------

LHO (East):
  Estimated HCP: 13.7
  Expected shape:
    ♠ 3.3
    ♥ 2.3
    ♦ 4.0
    ♣ 3.4

Partner (South):
  Estimated HCP: 9.8
  Expected shape:
    ♠ 3.0
    ♥ 2.6
    ♦ 3.7
    ♣ 3.7

RHO (West):
  Estimated HCP: 9.3
  Expected shape:
    ♠ 2.0
    ♥ 5.4
    ♦ 3.3
    ♣ 2.3
```

**Interpretation**: East (dummy) has invitational values, West (declarer) is surprisingly weak with long hearts, Partner has scattered values.

### 2. Competitive Auction Analysis

You're East after a competitive sequence with takeout double.

```bash
python uday/hand_inference_standalone.py "AQ32.K5.Q987.K32" \
  --auction "1C X 1H PASS 2H" \
  --seat E --dealer N --vuln NS \
  --model models/TF2models/BEN-Sayc-Info-8730_2025-04-20-E30.keras
```

**Output**:
```
============================================================
HAND INFERENCE RESULTS
============================================================
Auction: 1C X 1H PASS 2H
Your seat: E | Dealer: N | Vulnerability: NS
------------------------------------------------------------

LHO (South):
  Estimated HCP: 10.6
  Expected shape:
    ♠ 2.4
    ♥ 4.1
    ♦ 2.1
    ♣ 4.4

Partner (West):
  Estimated HCP: 11.3
  Expected shape:
    ♠ 3.8
    ♥ 1.7
    ♦ 4.6
    ♣ 2.9

RHO (North):
  Estimated HCP: 4.3
  Expected shape:
    ♠ 2.8
    ♥ 4.7
    ♦ 3.0
    ♣ 2.4
```

**Interpretation**: Partner made takeout double with 11+ HCP and shortness in hearts, North has minimum opener with hearts/clubs, South has heart support.

### 3. Opening Lead Decision

You're West on lead against 4♠. Auction gives clues about hand distributions.

```bash
python uday/hand_inference_standalone.py "76.AQJ4.K532.Q87" \
  --auction "1S PASS 2NT PASS 3C PASS 3S PASS 4S PASS PASS PASS" \
  --seat W --dealer N \
  --model models/TF2models/BEN-21GF-Info-8730_2025-04-18-E30.keras
```

This helps you understand:
- How strong North (opener) is
- What East (your partner) likely has  
- What South (responder) showed with 2NT and 3S

### 4. Slam Investigation

You're South in a slam-going auction and want to understand partner's likely holdings.

```bash
python uday/hand_inference_standalone.py "AK432.5.AQJ7.K43" \
  --auction "1S PASS 2C PASS 2H PASS 4NT PASS 5D" \
  --seat S --dealer N \
  --model models/TF2models/BEN-21GF-Info-8730_2025-04-18-E30.keras
```

### 5. After Opening Lead (With Dummy Visible)

**Note**: Current version doesn't support dummy input yet, but here's how you'd use it when that feature is added:

```bash
python uday/hand_inference_standalone.py "KJ5.Q987.432.J65" \
  --auction "1NT PASS 3NT PASS PASS PASS" \
  --seat N --dealer W \
  --dummy "Q104.K43.QJ10.KQ107" \
  --model models/TF2models/BEN-Sayc-Info-8730_2025-04-20-E30.keras
```

This would give much more accurate inference about declarer and partner since dummy is visible.

### 6. JSON Output for Analysis Tools

For integration with other tools or detailed analysis:

```bash
python uday/hand_inference_standalone.py "KJ5.Q987.432.J65" \
  --auction "1NT PASS 3NT PASS PASS PASS" \
  --seat N --dealer W --json \
  --model models/TF2models/BEN-Sayc-Info-8730_2025-04-20-E30.keras | \
  python -c "import json, sys; data=json.load(sys.stdin); print(f'Partner HCP: {data[\"predictions\"][\"Partner\"][\"hcp\"]:.1f}')"
```

### 7. Different Vulnerabilities

Vulnerability affects bidding, so specify it when relevant:

```bash
python uday/hand_inference_standalone.py "AJ1097.K3.AQ6.K42" \
  --auction "PASS PASS 3H X PASS 3S PASS 4S PASS PASS PASS" \
  --seat E --dealer N --vuln Both \
  --model models/TF2models/BEN-Sayc-Info-8730_2025-04-20-E30.keras
```

### 8. Preemptive Auctions

Understanding weak opening hands:

```bash
python uday/hand_inference_standalone.py "A5.KQ9.AKJ74.Q32" \
  --auction "3H X PASS 3NT PASS PASS PASS" \
  --seat E --dealer W --vuln NS \
  --model models/TF2models/BEN-Sayc-Info-8730_2025-04-20-E30.keras
```

### 9. Model Comparison

Compare how different systems interpret the same auction:

```bash
# SAYC interpretation
python uday/hand_inference_standalone.py "KJ5.Q987.432.J65" \
  --auction "1NT PASS 2C PASS 2H PASS 3NT" --seat N --dealer W \
  --model models/TF2models/BEN-Sayc-Info-8730_2025-04-20-E30.keras

# 2/1 GF interpretation  
python uday/hand_inference_standalone.py "KJ5.Q987.432.J65" \
  --auction "1NT PASS 2C PASS 2H PASS 3NT" --seat N --dealer W \
  --model models/TF2models/BEN-21GF-Info-8730_2025-04-18-E30.keras
```

Different systems may interpret 2C and the subsequent bidding differently.

## Tips for Best Results

1. **Choose the right model** for the bidding system being used
2. **Include vulnerability** when it matters (affects light openings, doubles, etc.)
3. **Use longer auctions** - more bidding gives better inference
4. **Consider the context** - model predictions are probabilistic estimates
5. **Shape predictions** are averages (3.2 spades likely means 3 or 4)
6. **HCP accuracy** improves with more specific auctions

## Common Patterns

- **1NT openings**: Usually show balanced hands with expected HCP range
- **Preempts**: Show long suits with appropriate weakness
- **Takeout doubles**: Indicate shortage in opponent's suit plus opening values
- **Jump responses**: Show specific strength ranges based on system
- **Competitive bidding**: Reveals more about shape and fit

The neural network has learned these patterns from millions of hands, so it can make sophisticated inferences that simple heuristics cannot.