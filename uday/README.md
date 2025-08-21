# Bidding Inference Tool

A Python program for making bidding predictions using Ben's neural network models.

## Requirements

- Python 3.7+
- TensorFlow >= 2.12 (required for loading `.keras` format models)
- NumPy

### Installation
```bash
pip install tensorflow>=2.12 numpy
```

**Important**: The Ben models are saved in Keras 3.x format (`.keras` files). These require TensorFlow 2.12 or newer. If you have an older version of TensorFlow, you'll need to upgrade:
```bash
pip install --upgrade tensorflow
```

## Usage

### Basic Command Structure
```bash
python bidding_inference.py <hand> <model_path> [options]
```

### Required Arguments
- `hand`: Bridge hand in PBN format (suits separated by dots: Spades.Hearts.Diamonds.Clubs)
- `model_path`: Path to the bidding model file

### Optional Arguments
- `--auction`: Space-separated auction sequence (e.g., "1C PASS 1H X" or "1NT PASS 2C")
  - Use X, DBL, D, or DOUBLE for double
  - Use XX, RDBL, RD, R, or REDOUBLE for redouble  
  - Use 10 or T for tens (automatically converted to T)
- `--vuln`: Vulnerability (None, NS, EW, Both)
- `--dealer`: Dealer position (N, E, S, W)
- `--seat`: Seat of the hand (N=North, E=East, S=South, W=West)
- `--n-cards`: Number of cards in model (24 for bidding, 32 for play, 52 for full deck, default auto-detected)
- `--model-version`: Model version (0-3, default 3)
- `--alert-supported`: Enable if model supports alerts

## Examples

### Opening Bid
```bash
python uday/bidding_inference.py "AK432.QJ9.K65.A7" models/TF2models/BEN-Sayc-8730_2025-04-20-E30.keras
```

### Response to 1C Opening
```bash
python uday/bidding_inference.py "QJ65.K1087.A3.954" models/TF2models/BEN-Sayc-8730_2025-04-20-E30.keras --auction "1C" --seat S
```

### Competitive Bidding with Double/Redouble
```bash
python uday/bidding_inference.py "AQJ10.K43.Q987.K2" models/TF2models/BEN-21GF-8730_2025-04-18-E30.keras --auction "1C X XX" --seat N
```

### Using 10s in Bids
```bash
python uday/bidding_inference.py "AQ109.K43.Q987.K2" models/TF2models/BEN-Sayc-8730_2025-04-20-E30.keras --auction "1N PASS 2C PASS 2H"
```

## Available Models

### SAYC System Models
- `BEN-Sayc-8730_2025-04-20-E30.keras`
- `BlueChip-Sayc-8712_2024-11-29-E25.keras`
- `Robo-Sayc-8730_2025-05-07-E30.keras`
- `Shark-Sayc-8730_2025-04-21-E30.keras`
- `WBridge5-Sayc-8730_2025-04-20-E30.keras`

### 2/1 Game Force Models
- `BEN-21GF-8730_2025-04-18-E30.keras`
- `LIA-21GF-8730_2025-04-19-E30.keras`
- `QPlus-21GF-8730_2025-04-21-E30.keras`

### Other Systems
- `GIB-BBO-8730_2025-04-19-E30.keras`

## Output

The program outputs:
1. The recommended bid with confidence percentage
2. Top 5 bid options with probabilities
3. Alert probability (if model supports alerts)

## Notes

- **TensorFlow Version**: The program requires TensorFlow 2.12+ to load the `.keras` format models
- **Card Count**: Bidding models use 24 cards (grouped pips: AKQJTx) while playing models use 32 cards  
- Models are trained on expert bridge play data
- Different models represent different bidding systems and styles
- Ensure the auction sequence matches the expected seat to bid
- The program automatically detects bidding models and sets n_cards=24 appropriately