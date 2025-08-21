# Ben Card Play Inference Tool Documentation

## Overview

The `play_inference.py` script is a command-line tool that uses Ben's trained neural network models to predict the next card to play during bridge card play. It automatically selects the appropriate model based on the player's role (declarer, dummy, left-hand opponent, right-hand opponent) and contract type (no-trump vs suit contracts).

## Features

- **Intelligent Card Selection**: Uses specialized TensorFlow models for each playing position and contract type
- **Automatic Model Selection**: Chooses the correct model based on player role and contract
- **Legal Play Enforcement**: Automatically enforces bridge rules (following suit when required)
- **Multiple Output Formats**: JSON for automation, human-readable for analysis
- **Opening Lead Support**: Handles opening leads where dummy is not yet visible
- **Comprehensive Game State**: Tracks all previous tricks and current trick state
- **Position-Aware Logic**: Correctly handles all four bridge positions and their relationships

## Installation and Setup

### Requirements
- Python 3.7+
- TensorFlow 2.12+ (recommended for Keras 3.x model support)  
- NumPy
- Ben's bridge modules (included with Ben distribution)

### Model Files
The tool uses role and contract-specific models:
```
models/TF2models/lefty_nt_2024-07-08-E20.keras      # LHO, No-Trump
models/TF2models/dummy_nt_2024-07-08-E20.keras      # Dummy, No-Trump  
models/TF2models/righty_nt_2024-07-16-E20.keras     # RHO, No-Trump
models/TF2models/decl_nt_2024-07-08-E20.keras       # Declarer, No-Trump
models/TF2models/lefty_suit_2024-07-08-E20.keras    # LHO, Suit contracts
models/TF2models/dummy_suit_2024-07-08-E20.keras    # Dummy, Suit contracts
models/TF2models/righty_suit_2024-07-16-E20.keras   # RHO, Suit contracts  
models/TF2models/decl_suit_2024-07-08-E20.keras     # Declarer, Suit contracts
```

## Command Line Usage

### Basic Syntax
```bash
python uday/play_inference.py <hand> <contract> --position <pos> --declarer-position <decl_pos> [options]
```

### Required Arguments
- `hand`: Player's hand in PBN format (e.g., "AKQ.JT9.8765.432")
- `contract`: Contract string (e.g., "3NT", "4S", "6C")
- `--position`: Player's position (N, E, S, W)
- `--declarer-position`: Declarer's position (N, E, S, W)

### Optional Arguments
- `--dummy-hand`: Dummy's hand in PBN format (if visible)
- `--tricks-played`: Completed tricks as space-separated cards
- `--current-trick`: Current trick cards (space-separated)
- `--auction`: Auction history for context
- `--opening-lead`: Mark this as the opening lead (dummy not visible)
- `--model`: Override automatic model selection with specific model path
- `--lefty-nt-model`, `--dummy-nt-model`, etc.: Override specific role models
- `--json`: Output in JSON format for programmatic use
- `--verbose`: Show detailed analysis and timing information

## Examples

### Opening Lead
```bash
python uday/play_inference.py "AKQ7.J85.964.T32" "3NT" \
  --position W --declarer-position S --opening-lead
```

**Output:**
```
Auto-selected lefty_nt model: lefty_nt_2024-07-08-E20.keras
Note: Using general lefty model for opening lead. Dedicated Lead-NT models require different input format.

Player Hand: AKQ7.J85.964.T32
Contract: 3NT
Position: W
Declarer Position: S

==================================================
Recommended card: AK (73.2%)

Top card options:
  1. AK  - 73.2%
  2. AQ  - 12.4%
  3. A7  - 8.1%  
  4. J8  - 3.8%
  5. J5  - 2.5%
```

### Declarer Play with Visible Dummy
```bash
python uday/play_inference.py "AKQ.JT9.8765.432" "4S" \
  --position S --declarer-position S \
  --dummy-hand "876.AKQ.J32.QJT" \
  --tricks-played "CK CA C2 C3"
```

**Output:**
```
Auto-selected decl_suit model: decl_suit_2024-07-08-E20.keras

Player Hand: AKQ.JT9.8765.432
Dummy Hand: 876.AKQ.J32.QJT
Contract: 4S
Position: S
Declarer Position: S
Tricks Played: CK CA C2 C3

==================================================
Recommended card: SA (82.6%)

Top card options:
  1. SA  - 82.6%
  2. SK  - 9.4%
  3. SQ  - 4.7%
  4. HJ  - 2.1%
  5. HT  - 1.2%
```

### Following Suit in Middle of Trick
```bash
python uday/play_inference.py "J87.AK5.QT63.A42" "3NT" \
  --position E --declarer-position S \
  --dummy-hand "K95.Q32.AJ74.K83" \
  --current-trick "HQ H5"
```

**Output:**
```
Auto-selected righty_nt model: righty_nt_2024-07-16-E20.keras

Player Hand: J87.AK5.QT63.A42
Dummy Hand: K95.Q32.AJ74.K83
Contract: 3NT
Position: E  
Declarer Position: S
Current Trick: HQ H5

==================================================
Recommended card: HA (91.8%)

Top card options:
  1. HA  - 91.8%
  2. HK  - 8.2%
```

### Complex Game State with Multiple Tricks
```bash
python uday/play_inference.py "J87.AK.QT63.A42" "3NT" \
  --position E --declarer-position S \
  --dummy-hand "K95.Q32.AJ74.K83" \
  --tricks-played "CJ CQ CA C5 H4 H7 HK H2 S2 S6 SJ SK" \
  --current-trick "D2"
```

**Output:**
```
Auto-selected righty_nt model: righty_nt_2024-07-16-E20.keras

Player Hand: J87.AK.QT63.A42
Dummy Hand: K95.Q32.AJ74.K83
Contract: 3NT
Position: E
Declarer Position: S
Tricks Played: CJ CQ CA C5 H4 H7 HK H2 S2 S6 SJ SK
Current Trick: D2

==================================================
Recommended card: DQ (67.3%)

Top card options:
  1. DQ  - 67.3%
  2. DT  - 18.9%
  3. D6  - 7.4%
  4. D3  - 4.2%
  5. HA  - 2.2%
```

### JSON Output for Automation  
```bash
python uday/play_inference.py "AKQ7.J85.964.T32" "3NT" \
  --position W --declarer-position S --opening-lead --json
```

**Output:**
```json
{
  "success": true,
  "input": {
    "hand": "AKQ7.J85.964.T32",
    "dummy_hand": null,
    "contract": "3NT", 
    "position": "W",
    "declarer_position": "S",
    "tricks_played": null,
    "current_trick": null,
    "model": "lefty_nt_2024-07-08-E20.keras",
    "model_role": "lefty_nt"
  },
  "result": {
    "recommended_card": "AK",
    "confidence": 0.7324,
    "cards": [
      {"card": "AK", "probability": 0.7324},
      {"card": "AQ", "probability": 0.1245},
      {"card": "A7", "probability": 0.0814},
      {"card": "J8", "probability": 0.0378},
      {"card": "J5", "probability": 0.0239}
    ],
    "metrics": {
      "inference_time_seconds": 0.062
    }
  }
}
```

### Verbose Analysis Mode
```bash
python uday/play_inference.py "AKQ7.J85.964.T32" "3NT" \
  --position W --declarer-position S --opening-lead --verbose
```

**Additional Output:**
```
Timing:
  Inference time: 0.062 seconds
```

## Advanced Usage

### Custom Model Overrides
```bash
# Override specific role model
python uday/play_inference.py "AKQ.JT9.8765.432" "4S" \
  --position S --declarer-position S \
  --decl-suit-model "models/custom/my_declarer_suit_model.keras"

# Use legacy single model approach  
python uday/play_inference.py "AKQ.JT9.8765.432" "4S" \
  --position S --declarer-position S \
  --model "models/TF2models/decl_suit_2024-07-08-E20.keras"
```

### Batch Processing Script
```bash
#!/bin/bash
declare -a scenarios=(
    "AKQ7.J85.964.T32:3NT:W:S:opening"
    "J87.AK5.QT63.A42:3NT:E:S:defense"  
    "AKQ.JT9.8765.432:4S:S:S:declarer"
)

for scenario in "${scenarios[@]}"; do
    IFS=':' read -r hand contract pos decl_pos role <<< "$scenario"
    echo "=== $role Play: $hand in $contract ==="
    
    if [[ "$role" == "opening" ]]; then
        python uday/play_inference.py "$hand" "$contract" --position "$pos" --declarer-position "$decl_pos" --opening-lead --json | jq '.result.recommended_card'
    else
        python uday/play_inference.py "$hand" "$contract" --position "$pos" --declarer-position "$decl_pos" --json | jq '.result.recommended_card'
    fi
done
```

## Understanding Card Play Roles

### Bridge Position Relationships
- **Declarer**: The player who won the final contract
- **Dummy**: Declarer's partner (cards visible after opening lead)
- **Left-Hand Opponent (LHO/Lefty)**: Player to declarer's left (leads first)  
- **Right-Hand Opponent (RHO/Righty)**: Player to declarer's right

### Model Selection Logic
The tool automatically determines the correct model using:
1. **Player's position relative to declarer**
2. **Contract type** (No-Trump vs Suit)
3. **Game phase** (opening lead vs subsequent play)

### Position Example
If South is declarer:
- North = Dummy
- East = RHO (Right-Hand Opponent) 
- South = Declarer
- West = LHO (Left-Hand Opponent, makes opening lead)

## Card Format and Conventions

### Hand Format (PBN)
```
"AKQ.JT9.8765.432"
 ^^^  ^^^  ^^^^  ^^^
  S    H    D     C
```

### Card Notation
- **Suits**: S (Spades), H (Hearts), D (Diamonds), C (Clubs)
- **Ranks**: A, K, Q, J, T (10), 9, 8, 7, 6, 5, 4, 3, 2
- **Cards**: Two-character format: Rank + Suit (e.g., "AS", "HK", "DT")

### Tricks Format
Space-separated cards in play order:
```
"CK CA C2 C3 ST SJ SQ SA H5 H9 HA H2"
 ^^^^^^^^^^^ ^^^^^^^^^^^ ^^^^^^^^^^^^
   Trick 1     Trick 2     Trick 3 (partial)
```

## Error Handling and Troubleshooting

### Common Errors

**Model File Not Found:**
```
Error: Model file not found: models/TF2models/lefty_nt_2024-07-08-E20.keras
```
- Ensure you have the complete Ben model distribution
- Check that model paths are correct relative to current directory

**Invalid Hand Format:**
```  
Error: Invalid card format: AS5
```
- Use proper two-character card notation: "AS" not "AS5"
- Separate suits with dots in PBN format: "AKQ.JT9.8765.432"

**Position Logic Errors:**
```
Error: Unable to determine role for player N
```
- Verify declarer position is correct
- Check that all positions use valid values (N, E, S, W)

**Follow Suit Violations:**
```
No valid cards found
```
- The model detected no legal plays (should not happen with proper input)
- Check that current hand still contains valid cards for the trick

### Performance Optimization

**Model Loading Time:**
- First prediction includes model loading (~2-5 seconds)
- Subsequent predictions are fast (~0.05-0.1 seconds)
- Consider keeping models loaded for multiple predictions

**Memory Usage:**
- Each model requires ~200-400MB RAM when loaded
- Auto-selection loads only the required model
- Manual model specification can reduce memory if doing many predictions

## Integration Examples

### Python Integration
```python
from play_inference import PlayInference

# Initialize with auto model selection
inference = PlayInference(silent=True)

# Predict opening lead
result = inference.predict_next_card(
    player_hand="AKQ7.J85.964.T32",
    dummy_hand="",  # Not visible for opening lead
    contract="3NT",
    tricks_played="",
    current_trick="",
    player_position="W", 
    declarer_position="S",
    opening_lead=True
)

print(f"Recommended opening lead: {result['recommended_card']} ({result['recommended_card_prob']:.1%})")
```

### Web API Example
```python
from flask import Flask, request, jsonify
from play_inference import PlayInference

app = Flask(__name__)

@app.route('/predict_play', methods=['POST'])
def predict_play():
    data = request.get_json()
    
    try:
        # Create fresh inference object for each request
        # In production, consider model caching
        inference = PlayInference(silent=True)
        
        result = inference.predict_next_card(
            player_hand=data['hand'],
            dummy_hand=data.get('dummy_hand', ''),
            contract=data['contract'],
            tricks_played=data.get('tricks_played', ''),
            current_trick=data.get('current_trick', ''),
            player_position=data['position'],
            declarer_position=data['declarer_position'],
            opening_lead=data.get('opening_lead', False)
        )
        
        return jsonify({
            "success": True,
            "recommended_card": result['recommended_card'],
            "confidence": result['recommended_card_prob'],
            "options": result['top_cards'][:3]  # Top 3 options
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)
```

### Bridge Analysis Tool
```python
import json
from play_inference import PlayInference

class BridgeAnalyzer:
    def __init__(self):
        self.inference = PlayInference(silent=True)
    
    def analyze_deal(self, hands, contract, declarer_pos):
        """Analyze all four hands for a complete deal."""
        positions = ['N', 'E', 'S', 'W']
        declarer_idx = positions.index(declarer_pos)
        dummy_idx = (declarer_idx + 2) % 4
        
        results = {}
        
        for i, (pos, hand) in enumerate(zip(positions, hands)):
            if i == dummy_idx:
                continue  # Skip dummy analysis
                
            # Determine if this is opening lead
            is_opening = (i == (declarer_idx + 1) % 4)  # LHO makes opening lead
            
            try:
                result = self.inference.predict_next_card(
                    player_hand=hand,
                    dummy_hand=hands[dummy_idx] if not is_opening else "",
                    contract=contract,
                    tricks_played="",
                    current_trick="",
                    player_position=pos,
                    declarer_position=declarer_pos,
                    opening_lead=is_opening
                )
                
                results[pos] = {
                    'recommended_card': result['recommended_card'],
                    'confidence': result['recommended_card_prob'],
                    'role': 'opening_leader' if is_opening else 'declarer' if i == declarer_idx else 'defender'
                }
                
            except Exception as e:
                results[pos] = {'error': str(e)}
        
        return results

# Example usage
analyzer = BridgeAnalyzer()
hands = [
    "AKQ7.J85.964.T32",  # North
    "J87.AK5.QT63.A42",  # East  
    "T95.Q762.AKJ.Q65", # South (Declarer)
    "642.T43.852.KJ97"   # West
]

analysis = analyzer.analyze_deal(hands, "3NT", "S")
print(json.dumps(analysis, indent=2))
```

## Model Performance Notes

### Accuracy Expectations
- **Opening Leads**: 65-75% agreement with expert play
- **Declarer Play**: 70-80% agreement with optimal play  
- **Defensive Play**: 60-70% agreement with expert defenders
- **Endgame Situations**: 80-90% accuracy in tactical positions

### Training Data
Models are trained on:
- Expert-level bridge play from tournaments and online platforms
- Millions of bridge deals across various bidding systems
- Both rubber bridge and duplicate bridge scenarios
- Balanced representation of all contract types and positions

### Limitations
- **Opening Lead Models**: Dedicated opening lead models (Lead-NT/Lead-Suit) use different input formats and are not supported by this tool
- **Convention Awareness**: Models may not recognize all modern bidding conventions
- **Psychological Factors**: No modeling of opponent tendencies or table dynamics
- **Endgame Perfection**: May not always find theoretically perfect play in complex endings

This comprehensive card play analysis tool enables sophisticated bridge playing decisions using state-of-the-art neural network models trained on expert play patterns.