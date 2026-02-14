# config.py
# Central place for imports, constants, environment variables, clients, and helpers
# Use: from config import *  in other files

import os
from datetime import datetime, timedelta
from pathlib import Path
import pytz
import pandas as pd
import numpy as np
import yfinance as yf

# Load environment variables from .env file
from dotenv import load_dotenv

# Try multiple locations for .env file
possible_env_paths = [
    Path.cwd() / ".env",                    # Current working directory
    Path(__file__).parent / ".env",         # Services directory
    Path(__file__).parent.parent / ".env",  # Root directory
]

env_path = None
for path in possible_env_paths:
    if path.exists():
        env_path = path
        break

if env_path:
    load_dotenv(dotenv_path=env_path)
    # Also manually read and set env vars as fallback for PyInstaller
    try:
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
    except Exception as e:
        print(f"Warning: Could not manually load .env: {e}")
else:
    print("WARNING: No .env file found in any expected location")

# TA-Lib with safe fallback
try:
    import talib
    TALIB_AVAILABLE = True
except ImportError:
    TALIB_AVAILABLE = False
    print("TA-Lib not found - using pandas EMA fallback for MACD")

# Alpaca imports (modern alpaca-py)
from alpaca.trading.client import TradingClient
from alpaca.data import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

# ML imports (expand later as needed)
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score, precision_score, recall_score
from sklearn.preprocessing import StandardScaler
import joblib
import schedule
import threading

# Logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ────────────────────────────────────────────────
#  LOAD SECRETS FROM ENVIRONMENT (.env file)
# ────────────────────────────────────────────────
API_KEY    = os.getenv("ALPACA_API_KEY")
API_SECRET = os.getenv("ALPACA_SECRET_KEY")

if not API_KEY or not API_SECRET:
    raise ValueError(
        "ALPACA_API_KEY and ALPACA_SECRET_KEY must be set in .env file. "
        "Copy .env.example and add your credentials!"
    )

PAPER_MODE = os.getenv("PAPER_MODE", "True").lower() in ("true", "1", "yes")

# Constants
TIMEZONE          = pytz.timezone('US/Eastern')
NUM_TOP_SYMBOLS   = 20
FETCH_TOP_BEFORE_FILTER = 50
MAX_PRICE_FILTER  = 20.0
MIN_PRICE_FILTER  = 1.0
DAYS_BACK         = 30
INTERVAL          = "1m"          # 1 minute bars
LOOKAHEAD_BARS    = 5
PROFIT_THRESHOLD  = 0.001         # 0.1%

# ─────────────────────────────────────────────────
#  ML / Trading Strategy Configuration
# ─────────────────────────────────────────────────
MODELS_DIR        = Path(__file__).parent / "models"
MODELS_DIR.mkdir(exist_ok=True)

LOGS_DIR          = Path(__file__).parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

TRADES_LOG_FILE   = LOGS_DIR / "trades.csv"  # Daily updated
STRATEGY_LOGS_DIR = LOGS_DIR / "strategies"
STRATEGY_LOGS_DIR.mkdir(exist_ok=True)

# Model configuration
ML_MODEL_TYPE     = os.getenv("ML_MODEL_TYPE", "random_forest")  # or "gradient_boosting"
MIN_TRAINING_SAMPLES = 500
MIN_CONFIDENCE    = 0.65            # Minimum prediction confidence to trade
TRAIN_TEST_SPLIT  = 0.2

# Risk management - Load from .env if present, otherwise use defaults
try:
    POSITION_SIZE_PCT = int(os.getenv("POSITION_SIZE_PCT", 50))
except ValueError:
    POSITION_SIZE_PCT = 50

try:
    MAX_OPEN_POSITIONS = int(os.getenv("MAX_OPEN_POSITIONS", 10))
except ValueError:
    MAX_OPEN_POSITIONS = 10

try:
    STOP_LOSS_PCT = float(os.getenv("STOP_LOSS_PCT", 0.02))
except ValueError:
    STOP_LOSS_PCT = 0.02

try:
    TAKE_PROFIT_PCT = float(os.getenv("TAKE_PROFIT_PCT", 0.04))
except ValueError:
    TAKE_PROFIT_PCT = 0.04

# Position sizing presets (as percentages of buying power)
POSITION_SIZE_PRESETS = [25, 50, 75, 100]  # Default presets for UI selector

# ─────────────────────────────────────────────────
#  Trading Strategies
# ─────────────────────────────────────────────────
STRATEGIES = {
    'macd_crossover': {
        'name': 'MACD Crossover',
        'description': 'Swing trading using MACD signals',
        'lookback_bars': 20,
        'min_confidence': 0.65,
        'risk_per_trade': 0.02,
        'enabled': True
    },
    'scalping': {
        'name': 'Scalping',
        'description': 'Quick trades capturing small moves (1-5 min)',
        'lookback_bars': 5,
        'min_confidence': 0.70,
        'risk_per_trade': 0.01,
        'enabled': True
    },
    'options_scalping': {
        'name': 'Options Scalping',
        'description': 'Scalping options contracts (EXPERIMENTAL)',
        'lookback_bars': 5,
        'min_confidence': 0.75,
        'risk_per_trade': 0.015,
        'enabled': False  # Not yet implemented
    },
    'five_pillars': {
        'name': 'Five Pillars',
        'description': 'Multi-factor analysis strategy (EXPERIMENTAL)',
        'lookback_bars': 50,
        'min_confidence': 0.75,
        'risk_per_trade': 0.02,
        'enabled': False  # Not yet implemented
    }
}

# Active strategy (can be switched)
ACTIVE_STRATEGY = 'macd_crossover'

# Market hours (US/Eastern)
MARKET_OPEN_HOUR   = 9              # 9:30 AM
MARKET_OPEN_MIN    = 30
MARKET_CLOSE_HOUR  = 16             # 4:00 PM
MARKET_CLOSE_MIN   = 0

# Training schedule (when market is closed)
TRAIN_TIME         = "20:00"        # 8 PM ET - after market close
REBALANCE_TIME     = "04:00"        # 4 AM ET - before market open

# Shared clients (created once here)
trade_client = TradingClient(API_KEY, API_SECRET, paper=PAPER_MODE)
data_client  = StockHistoricalDataClient(API_KEY, API_SECRET)

# Helpers
def now_eastern():
    return datetime.now(TIMEZONE)

def get_date_range(days_back=DAYS_BACK):
    end   = now_eastern()
    start = end - timedelta(days=days_back * 1.5)  # buffer for weekends/holidays
    return start, end

def save_settings_to_env(settings_dict):
    """
    Save trading settings to .env file for persistence across restarts.
    
    Args:
        settings_dict: Dictionary of settings to save
            - position_size_pct: percentage of buying power to use per position
            - stop_loss_pct: stop loss percentage
            - take_profit_pct: take profit percentage
            - max_open_positions: max concurrent positions
            - ml_model_type: "random_forest" or "gradient_boosting"
            - strategy_min_confidence: minimum confidence for current strategy
    
    Returns:
        bool: True if successful, False otherwise
    """
    global env_path, POSITION_SIZE_PCT, STOP_LOSS_PCT, TAKE_PROFIT_PCT, MAX_OPEN_POSITIONS, ML_MODEL_TYPE
    
    if not env_path or not env_path.exists():
        logger.error("Cannot save settings: .env file not found")
        return False
    
    try:
        # Read current .env file
        env_vars = {}
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
        
        # Update with new settings
        if 'position_size_pct' in settings_dict:
            env_vars['POSITION_SIZE_PCT'] = str(settings_dict['position_size_pct'])
            POSITION_SIZE_PCT = settings_dict['position_size_pct']
        
        if 'stop_loss_pct' in settings_dict:
            env_vars['STOP_LOSS_PCT'] = str(settings_dict['stop_loss_pct'])
            STOP_LOSS_PCT = settings_dict['stop_loss_pct']
        
        if 'take_profit_pct' in settings_dict:
            env_vars['TAKE_PROFIT_PCT'] = str(settings_dict['take_profit_pct'])
            TAKE_PROFIT_PCT = settings_dict['take_profit_pct']
        
        if 'max_open_positions' in settings_dict:
            env_vars['MAX_OPEN_POSITIONS'] = str(settings_dict['max_open_positions'])
            MAX_OPEN_POSITIONS = settings_dict['max_open_positions']
        
        if 'ml_model_type' in settings_dict:
            env_vars['ML_MODEL_TYPE'] = settings_dict['ml_model_type']
            ML_MODEL_TYPE = settings_dict['ml_model_type']
        
        # Write back to .env file
        with open(env_path, 'w') as f:
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")
        
        logger.info(f"Settings saved to {env_path}")
        return True
    
    except Exception as e:
        logger.error(f"Error saving settings: {e}")
        return False

logger.info("config.py loaded successfully")