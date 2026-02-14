# config.py
# Central place for imports, constants, environment variables, clients, and helpers
# Use: from config import *  in other files

import os
from datetime import datetime, timedelta
import pytz
import pandas as pd
import numpy as np
import yfinance as yf

# TA-Lib with safe fallback
try:
    import talib
    TALIB_AVAILABLE = True
except ImportError:
    TALIB_AVAILABLE = False
    print("TA-Lib not found → using pandas EMA fallback for MACD")

# Alpaca imports (modern alpaca-py)
from alpaca.trading.client import TradingClient
from alpaca.data import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

# ML imports (expand later as needed)
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

# Logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ────────────────────────────────────────────────
#  LOAD SECRETS FROM ENVIRONMENT (Replit Secrets / .env / system)
# ────────────────────────────────────────────────
API_KEY    = os.getenv("PKQMM67ATX7PJJMNXGORAAY2D6")
API_SECRET = os.getenv("Gi5WaGkJr9GpbGezszkhA8t3jkL2WysxnV4QpQi7B8Un")

if not API_KEY or not API_SECRET:
    raise ValueError(
        "ALPACA_API_KEY and ALPACA_SECRET_KEY must be set in Replit Secrets "
        "or as environment variables. Do NOT hardcode them!"
    )

PAPER_MODE = True   # Change to False only when using LIVE keys

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