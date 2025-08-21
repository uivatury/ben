# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BEN (Bridge ENgine) is a machine learning-based bridge game engine that can play as a robot, perform analysis, and help develop bridge AI. It uses neural networks (TensorFlow/Keras) and double dummy solver for decision making in bidding, opening leads, and card play.

## Environment Setup

This project runs on Python 3.12 with TensorFlow 2.18. Dependencies are managed via `pyproject.toml`:

```bash
# Activate the virtual environment
source ~/ben-env/bin/activate
pip install -r requirements.txt
```

## Development Commands

**IMPORTANT: Always activate the virtual environment first before running any commands:**
```bash
source ~/ben-env/bin/activate
```

### Starting the Game Services

```bash
# Activate environment first!
source ~/ben-env/bin/activate

# Navigate to src directory (from /home/ben/ben)
cd src

# Start game server (handles bot API via websockets)
python gameserver.py
# Or with specific boards:
python gameserver.py --boards file.pbn --boardno <number>

# Start app server (serves UI via HTTP) - in a new terminal
source ~/ben-env/bin/activate
cd /home/ben/ben/src/frontend
python appserver.py
# Access at: http://127.0.0.1:8080/home
```

### Starting API Server

```bash
# Activate environment first!
source ~/ben-env/bin/activate
cd /home/ben/ben/src
python gameapi.py  # Listens on port 8085 by default
# Override config: python gameapi.py --config <config_file>
# Override port: python gameapi.py --port <port_number>
```

### Running Self-Play Games

```bash
# Activate environment first!
source ~/ben-env/bin/activate
cd /home/ben/ben/src
python game.py  # Plays games against itself
# With specific boards: python game.py --boards file.pbn
```

### Connecting to Table Manager

```bash
# Activate environment first!
source ~/ben-env/bin/activate
cd /home/ben/ben/src
python table_manager_client.py --host 127.0.0.1 --port 2000 --name BEN --seat North
```

## Architecture Overview

### Core Components

1. **Neural Network Models** (`src/nn/`)
   - `bidder_tf2.py` - Bidding decisions
   - `leader_tf2.py` - Opening lead selection
   - `player_tf2.py` - Card play during the game
   - `contract_tf2.py` - Contract evaluation
   - `trick_tf2.py` - Trick prediction
   - Models stored in `models/TF2models/` as `.keras` files

2. **Game Logic** (`src/`)
   - `game.py` - Main game loop and coordination
   - `gameapi.py` - REST API server for external integrations
   - `gameserver.py` - WebSocket server for real-time game play
   - `botbidder.py` - Bot bidding logic
   - `botopeninglead.py` - Bot opening lead logic
   - `botcardplayer.py` - Bot card playing logic

3. **Bridge Systems** (`src/bba/`)
   - Bridge Bidding Analyzer for convention card interpretation
   - Handles different bidding systems (SAYC, 21GF, etc.)

4. **Configuration** (`src/config/`)
   - System configurations for different bots and conventions
   - Format: `.conf` files with model paths and system settings

5. **Double Dummy Solver** (`src/ddsolver/`)
   - Integration with DDS library for perfect play analysis
   - Used for training and evaluation

6. **Frontend** (`src/frontend/`)
   - Web UI components
   - `appserver.py` - Flask server for UI
   - HTML/JS files for browser interface

### API Endpoints

- `/bid` - Get bidding recommendation
- `/lead` - Get opening lead recommendation  
- `/play` - Get card play recommendation

Parameters include: `ctx` (bidding context), `hand`, `user`, `dealer`, `seat`, `vul`, `dummy`, `played`, `tournament`

### Board Formats

- PBN (Portable Bridge Notation) - Standard format
- BEN internal format - Custom format for training data

### Key Conventions

- Uses PBN notation for hands and cards
- Bidding: Pass = "--", Double = "Db", Redouble = "Rd"
- Vulnerability: blank (none), @v (NS), @V (EW), @v@V (both)
- Seats: N, S, E, W

## Important Notes

- Models are pre-trained and stored in `models/TF2models/`
- Configuration files in `src/config/` determine which models and conventions to use
- The system requires matching bidding conventions between training and usage
- Logs are stored in `src/logs/`
- Example notebooks in `src/examples/` demonstrate API usage