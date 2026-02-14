# config.py
# Central place for all imports, keys, constants, and shared setups
# Import this file early in every script: from config import *

import os
from datetime import datetime, timedelta
import pytz
import pandas as pd
import numpy as np
import yfinance as yf

# Try to import TA-Lib; fallback to pandas if it fails
try:
    import talib
    TALIB_AVAILABLE = True
except ImportError:
    TALIB_AVAILABLE = False
    print("TA-Lib not installed → using pandas fallbacks for indicators")

# Alpaca & trading related
from alpaca.trading.client import TradingClient
from alpaca.data import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.common.requests import GetRequest  # If needed for custom endpoints

# ML & utils (add more as project grows)
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

# Constants & settings (easy to change here)
API_KEY = os.getenv("ALPACA_API_KEY", "YOUR_PAPER_KEY_HERE")
API_SECRET = os.getenv("ALPACA_SECRET_KEY", "YOUR_PAPER_SECRET_HERE")
PAPER_MODE = True

NUM_TOP_SYMBOLS = 20
DAYS_BACK = 30
INTERVAL = "1m"
LOOKAHEAD_BARS = 5
PROFIT_THRESHOLD = 0.001  # 0.1%

TIMEZONE = pytz.timezone('US/Eastern')

# Shared clients (initialize once)
trade_client = TradingClient(API_KEY, API_SECRET, paper=PAPER_MODE)
data_client = StockHistoricalDataClient(API_KEY, API_SECRET)

# Optional: quick helper functions everyone uses
def now_eastern():
    return datetime.now(TIMEZONE)

def get_date_range(days_back=DAYS_BACK):
    end = now_eastern()
    start = end - timedelta(days=days_back * 1.5)
    return start, end

# Logging setup (optional but very useful for bots)
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

print("config.py loaded successfully")