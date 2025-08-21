# Ben Bidding Inference Tool Documentation

## Overview

The `bidding_inference.py` script is a command-line tool that uses Ben's trained neural network models to predict the next bid in a bridge auction. It provides both programmatic (JSON) and human-readable output formats, making it suitable for both automated analysis and manual use.

## Features

- **Intelligent Bidding Predictions**: Uses TensorFlow 2.x models to predict the most likely next bid
- **Multiple Output Formats**: JSON for programmatic use, human-readable for manual analysis
- **Comprehensive Auction Support**: Handles all standard bridge bids including passes, doubles, and redoubles
- **Vulnerability Handling**: Supports all vulnerability conditions (None, NS, EW, Both)
- **Position-Aware**: Correctly handles dealer and seat positions in auction context
- **Model Flexibility**: Supports different model versions and alert-capable models
- **Confidence Analysis**: Provides probability scores and entropy measures

## Installation and Setup

### Requirements
- Python 3.7+
- TensorFlow 2.12+ (recommended for Keras 3.x model support)
- NumPy
- Ben's bridge modules (included with Ben distribution)

### Model Files
The tool requires trained bidding models in Keras format (`.keras` files). Example models:
```
models/TF2models/BEN-Sayc-8730_2025-04-20-E30.keras
models/TF2models/BEN-Precision-8730_2024-12-15-E30.keras
```

## Command Line Usage

### Basic Syntax
```bash
python uday/bidding_inference.py <hand> <model_path> [options]
```

### Required Arguments
- `hand`: Hand in PBN format (e.g., "AKQ.JT9.8765.432")
- `model`: Path to the bidding model file

### Optional Arguments
- `--auction`: Space-separated auction sequence (e.g., "1C PASS 1H PASS")
- `--vuln`: Vulnerability condition (None, NS, EW, Both/All)
- `--dealer`: Dealer position (N, E, S, W) 
- `--seat`: Position of the hand (N, E, S, W)
- `--n-cards`: Number of cards in model (24, 32, 52) - auto-detected for bidding models
- `--model-version`: Model version (0, 1, 2, 3)
- `--alert-supported`: Enable if model supports conventional alerts
- `--json`: Output in JSON format for programmatic use
- `--verbose`: Show detailed analysis (entropy, timing, etc.)

## Examples

### Basic Opening Bid Prediction
```bash
python uday/bidding_inference.py "AKQ.JT9.8765.432" models/TF2models/BEN-Sayc-8730_2025-04-20-E30.keras
```

**Output:**
```
Hand: AKQ.JT9.8765.432
Auction: (opening bid)
Vulnerability: None
Dealer: N
Seat: N

==================================================
Recommended bid: 1NT (85.2%)

Top 5 bid options:
  1. 1NT   - 85.2%
  2. 1D    - 8.1%
  3. 1C    - 4.2%
  4. 2NT   - 1.8%
  5. PASS  - 0.7%
```

### Response in Auction Sequence
```bash
python uday/bidding_inference.py "J87.AK5.QT63.A42" models/TF2models/BEN-Sayc-8730_2025-04-20-E30.keras \
  --auction "1C PASS 1D PASS 1NT PASS" --seat S --dealer N
```

**Output:**
```
Hand: J87.AK5.QT63.A42
Auction: 1C PASS 1D PASS 1NT PASS
Vulnerability: None
Dealer: N
Seat: S

==================================================
Recommended bid: 3NT (67.4%)

Top 5 bid options:
  1. 3NT   - 67.4%
  2. PASS  - 18.9%
  3. 2NT   - 7.3%
  4. 2C    - 4.1%
  5. 2D    - 2.3%
```

### Competitive Bidding with Vulnerability
```bash
python uday/bidding_inference.py "KQJ98.A6.752.K43" models/TF2models/BEN-Sayc-8730_2025-04-20-E30.keras \
  --auction "1C X PASS" --vuln EW --seat W --dealer N
```

**Output:**
```
Hand: KQJ98.A6.752.K43
Auction: 1C X PASS
Vulnerability: EW
Dealer: N
Seat: W

==================================================
Recommended bid: 1S (78.6%)

Top 5 bid options:
  1. 1S    - 78.6%
  2. PASS  - 12.4%
  3. 1NT   - 5.8%
  4. XX    - 2.1%
  5. 2S    - 1.1%
```

### JSON Output for Automation
```bash
python uday/bidding_inference.py "AKQ.JT9.8765.432" models/TF2models/BEN-Sayc-8730_2025-04-20-E30.keras --json
```

**Output:**
```json
{
  "success": true,
  "input": {
    "hand": "AKQ.JT9.8765.432",
    "auction": null,
    "vulnerability": "None",
    "dealer": "N",
    "seat": "N",
    "model": "BEN-Sayc-8730_2025-04-20-E30.keras"
  },
  "result": {
    "recommended_bid": "1NT",
    "confidence": 0.8523,
    "bids": [
      {"bid": "1NT", "probability": 0.8523},
      {"bid": "1D", "probability": 0.0814},
      {"bid": "1C", "probability": 0.0425},
      {"bid": "2NT", "probability": 0.0178},
      {"bid": "PASS", "probability": 0.0067}
    ],
    "metrics": {
      "entropy": 0.6847,
      "max_probability": 0.8523,
      "top5_total_probability": 0.9007,
      "inference_time_seconds": 0.045
    }
  }
}
```

### Verbose Analysis Mode
```bash
python uday/bidding_inference.py "AKQ.JT9.8765.432" models/TF2models/BEN-Sayc-8730_2025-04-20-E30.keras --verbose
```

**Additional Output:**
```
Confidence Analysis:
  Max probability: 85.2%
  Top 5 total: 90.1%
  Entropy: 0.68 (lower = more confident)
  Inference time: 0.045 seconds
```

## Advanced Usage

### Working with Different Bidding Systems
```bash
# Standard American (SAYC)
python uday/bidding_inference.py "AKQ.JT9.8765.432" models/TF2models/BEN-Sayc-8730_2025-04-20-E30.keras

# Precision Club
python uday/bidding_inference.py "AKQ.JT9.8765.432" models/TF2models/BEN-Precision-8730_2024-12-15-E30.keras
```

### Alert-Supported Models
```bash
python uday/bidding_inference.py "AKQ.JT9.8765.432" models/TF2models/BEN-Alerts-8730_2025-01-10-E30.keras \
  --alert-supported
```

### Batch Processing with JSON
```bash
#!/bin/bash
hands=("AKQ.JT9.8765.432" "J87.AK5.QT63.A42" "KQJ98.A6.752.K43")
model="models/TF2models/BEN-Sayc-8730_2025-04-20-E30.keras"

for hand in "${hands[@]}"; do
    echo "Processing hand: $hand"
    python uday/bidding_inference.py "$hand" "$model" --json | jq '.result.recommended_bid'
done
```

## Understanding the Output

### Probability Interpretation
- **High Confidence (>70%)**: Model is very certain about the recommended bid
- **Medium Confidence (30-70%)**: Multiple reasonable options exist
- **Low Confidence (<30%)**: Difficult decision, manual review recommended

### Entropy Metrics
- **Low Entropy (<1.0)**: Clear-cut decision with one dominant choice
- **Medium Entropy (1.0-2.0)**: Several viable options
- **High Entropy (>2.0)**: Many possibilities, uncertain situation

### Common Bid Abbreviations
- **PASS**: Pass (no bid)
- **X**: Double
- **XX**: Redouble
- **1C, 1D, 1H, 1S**: One-level suit bids
- **1NT, 2NT, etc.**: No-trump bids

## Error Handling

### Common Errors and Solutions

**Model Loading Failures:**
```
Error: Model file not found: models/missing.keras
```
- Verify the model file path exists
- Ensure you have the correct Ben model distribution

**TensorFlow Version Issues:**
```
Error loading model: Keras 3.x format requires newer TensorFlow
```
- Upgrade TensorFlow: `pip install tensorflow>=2.12`

**Invalid Auction Sequences:**
```
Error: It's not S's turn to bid. Expected E to bid
```
- Check auction sequence matches the dealer and seat positions
- Verify auction follows proper bridge bidding order

**Hand Format Errors:**
```
Error: Invalid hand format: AKQ.JT9.8765
```
- Use PBN format with dots separating suits: "AKQ.JT9.8765.432"
- Include all four suits even if empty: "AKQ.JT9.8765.-"

## Integration Examples

### Python Integration
```python
from bidding_inference import BiddingInference

# Initialize inference engine
inference = BiddingInference("models/TF2models/BEN-Sayc-8730_2025-04-20-E30.keras")

# Predict next bid
result = inference.predict_bid(
    hand_str="AKQ.JT9.8765.432",
    auction="1C PASS 1D PASS",
    vuln="None",
    dealer="N",
    seat="S"
)

print(f"Recommended bid: {result['top_bid']} ({result['top_bid_prob']:.1%})")
```

### Web API Integration
```python
import json
from flask import Flask, request, jsonify
from bidding_inference import BiddingInference

app = Flask(__name__)
inference = BiddingInference("models/TF2models/BEN-Sayc-8730_2025-04-20-E30.keras", silent=True)

@app.route('/predict_bid', methods=['POST'])
def predict_bid():
    data = request.get_json()
    try:
        result = inference.predict_bid(
            hand_str=data['hand'],
            auction=data.get('auction', ''),
            vuln=data.get('vulnerability', 'None'),
            dealer=data.get('dealer', 'N'),
            seat=data.get('seat', 'N')
        )
        return jsonify({"success": True, "result": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400
```

## Performance Considerations

- **Model Loading**: First prediction includes model loading time (~2-5 seconds)
- **Subsequent Predictions**: Very fast (~0.01-0.05 seconds per prediction)
- **Memory Usage**: Models require ~100-500MB RAM when loaded
- **GPU Acceleration**: Automatically uses GPU if available and configured

## Troubleshooting

### Performance Issues
- Ensure TensorFlow is properly installed with GPU support if desired
- Use `TF_CPP_MIN_LOG_LEVEL=2` to reduce TensorFlow logging overhead

### Model Compatibility
- Ben's bidding models typically use 24 cards (grouped pips)
- The tool auto-detects this for bidding models
- Use `--n-cards 24` explicitly if auto-detection fails

### Debugging Mode
Add verbose output to see detailed model predictions:
```bash
python uday/bidding_inference.py "AKQ.JT9.8765.432" model.keras --verbose --json | jq '.result.all_bids'
```

This comprehensive tool enables sophisticated bridge bidding analysis using state-of-the-art neural network models trained on expert play data.