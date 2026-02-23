# config.py - FIXED FOR .EXE BUNDLES
import os
import sys
from pathlib import Path
import pytz
import pandas as pd
import numpy as np
import yfinance as yf
from dotenv import load_dotenv

# === PYINSTALLER BUNDLE SUPPORT ===
if getattr(sys, 'frozen', False):
    # Running as .exe (frozen)
    base_path = Path(sys._MEIPASS)
else:
    # Normal Python run
    base_path = Path(__file__).parent.parent

# Look for .env in multiple places
env_paths = [
    base_path / ".env",
    base_path / "services" / ".env",
    Path.cwd() / ".env",
    Path.cwd() / "services" / ".env",
    ]

env_path = next((p for p in env_paths if p.exists()), None)

if env_path:
    load_dotenv(env_path)
    print(f"✅ Loaded .env from: {env_path}")
else:
    print("⚠️ WARNING: .env file not found! Alpaca keys missing.")

# Rest of your config (unchanged)
TIMEZONE = pytz.timezone('US/Eastern')
MODELS_DIR = Path(__file__).parent / "models"
MODELS_DIR.mkdir(exist_ok=True)
KNOWLEDGE_BASE = MODELS_DIR / "knowledge_base.json"

# ... (keep ALL the rest of your config.py exactly as it is from before) ...

logger.info("✅ config.py loaded with 7-agent system")