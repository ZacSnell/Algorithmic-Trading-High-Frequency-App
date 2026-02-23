# config.py
import os
from datetime import datetime, timedelta
from pathlib import Path
import pytz
import pandas as pd
import numpy as np
import yfinance as yf
from dotenv import load_dotenv

# Load .env
possible_env_paths = [Path.cwd() / ".env", Path(__file__).parent / ".env", Path(__file__).parent.parent / ".env"]
env_path = next((p for p in possible_env_paths if p.exists()), None)
if env_path:
    load_dotenv(env_path)

# TA-Lib fallback
try:
    import talib
    TALIB_AVAILABLE = True
except ImportError:
    TALIB_AVAILABLE = False

from alpaca.trading.client import TradingClient
from alpaca.data import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

API_KEY = os.getenv("ALPACA_API_KEY")
API_SECRET = os.getenv("ALPACA_SECRET_KEY")
PAPER_MODE = os.getenv("PAPER_MODE", "True").lower() in ("true", "1", "yes")

TIMEZONE = pytz.timezone('US/Eastern')
MODELS_DIR = Path(__file__).parent / "models"
MODELS_DIR.mkdir(exist_ok=True)
KNOWLEDGE_BASE = MODELS_DIR / "knowledge_base.json"
HISTORICAL_EVENTS_FILE = MODELS_DIR / "historical_events.json"

TRADE_CLIENT = TradingClient(API_KEY, API_SECRET, paper=PAPER_MODE)
DATA_CLIENT = StockHistoricalDataClient(API_KEY, API_SECRET)

SPECIALISTS = {
    'momentum': {'name': 'Momentum Agent', 'type': 'ml', 'features': ['MACD', 'MACD_Hist', 'RSI', 'ADX'], 'model_type': 'random_forest', 'min_confidence': 0.68},
    'reversion': {'name': 'Mean-Reversion Agent', 'type': 'ml', 'features': ['Bollinger_Width', 'RSI', 'ZScore'], 'model_type': 'gradient_boosting', 'min_confidence': 0.72},
    'volume': {'name': 'Volume Agent', 'type': 'ml', 'features': ['Volume', 'Volume_SMA_Ratio', 'OBV'], 'model_type': 'random_forest', 'min_confidence': 0.65},
    'volatility': {'name': 'Volatility Agent', 'type': 'ml', 'features': ['ATR', 'Bollinger_Width', 'Volatility_Ratio'], 'model_type': 'gradient_boosting', 'min_confidence': 0.70},
    'breakout': {'name': 'Breakout Agent', 'type': 'ml', 'features': ['High_Low_Range', 'Close_vs_High', 'Volume'], 'model_type': 'random_forest', 'min_confidence': 0.67},
    'news_catalyst': {'name': 'News Catalyst Agent', 'type': 'news', 'min_confidence': 0.60},
    'twitter_sentiment': {'name': 'Twitter Sentiment Agent', 'type': 'twitter', 'min_confidence': 0.60},
}

MIN_CONFIDENCE = 0.60
POSITION_SIZE_PCT = 50
MAX_OPEN_POSITIONS = 10
STOP_LOSS_PCT = 0.02
TAKE_PROFIT_PCT = 0.04
LOOKAHEAD_BARS = 5
PROFIT_THRESHOLD = 0.001
TRAIN_TEST_SPLIT = 0.2

logger.info("✅ config.py loaded with 7-agent system")