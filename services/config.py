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
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

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
ML_MODEL_TYPE     = "random_forest"  # or "gradient_boosting"
MIN_TRAINING_SAMPLES = 500
MIN_CONFIDENCE    = 0.65            # Minimum prediction confidence to trade
TRAIN_TEST_SPLIT  = 0.2

# Risk management
POSITION_SIZE_PCT = 50              # % of buying power to use per position (25/50/75/100 presets or custom)
MAX_OPEN_POSITIONS = 10             # Max concurrent positions
STOP_LOSS_PCT     = 0.02            # 2% stop loss
TAKE_PROFIT_PCT   = 0.04            # 4% take profit

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

logger.info("config.py loaded successfully")