# test_connection.py
import sys
from pathlib import Path

# Add parent directory to path so we can import config
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import *

# Quick test
try:
    account = trade_client.get_account()
    print("Connected to PAPER account!")
    print(f"Account ID: {account.account_number}")
    print(f"Buying Power: ${account.buying_power}")
    print(f"Equity: ${account.equity}")
except Exception as e:
    print("Connection failed:", e)