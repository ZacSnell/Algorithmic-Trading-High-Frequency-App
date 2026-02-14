# test_connection.py
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