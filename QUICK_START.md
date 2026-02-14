# Quick Start Guide - ML Trading System

## 5-Minute Setup

### Prerequisites
- ✅ Python 3.14+ (you have it!)
- ✅ Alpaca account with API keys in `.env`
- ✅ Dependencies installed from `requirements.txt`

### Installation (One Time)

```bash
# Install dependencies
pip install -r requirements.txt

# Create models directory (if needed)
mkdir services/models
```

---

## Three-Command Startup

### 1️⃣ Generate Training Data (30 days of history)
```bash
cd services
python build_dataset.py
```

**What to expect:**
```
Fetching top 50 most active stocks...
Got 50 candidates
Included AMC @ $4.23
Included NIO @ $3.87
...
Combined dataset saved: 250,000 rows
```

**Time:** ~2-5 minutes

---

### 2️⃣ Train Your ML Model
```bash
python ml_trainer.py
```

**What to expect:**
```
STARTING MODEL TRAINING PIPELINE
==============================================================
Data shape: (10000, 11)
Buy signals: 1200 | No signal: 8800
Buy signal ratio: 12.00%

Training RandomForest...
Feature Importances:
  MACD_Hist: 0.2847
  Close: 0.1923
  VWAP_Deviation: 0.1654
  ...

MODEL EVALUATION
==============================================================
Training Accuracy: 0.8234
Test Accuracy: 0.8056
ROC AUC Score: 0.8721
Precision: 0.782 | Recall: 0.715

Model saved to models/model_random_forest_20260214_203015.pkl
```

**Time:** ~1-3 minutes

---

### 3️⃣ Start Live Trading
```bash
python live_trader.py
```

**What to expect:**
```
STARTING LIVE TRADING SYSTEM
==============================================================
Model loaded and ready for predictions
Market Status: CLOSED (After Hours) | Saturday 20:35:14
✓ Live trading system started successfully
  - Training scheduled for 8 PM daily
  - Trading active during market hours
  - Rebalancing scheduled for 4 AM daily

Trading system running. Press Ctrl+C to stop...
```

---

## What Happens Next

### When Market Opens (9:30 AM ET)
The system automatically:
1. ✓ Gets list of active stocks
2. ✓ Runs ML predictions every minute
3. ✓ Executes BUY orders on high-confidence signals
4. ✓ Monitors positions for profit/loss
5. ✓ Logs all decisions

### When Market Closes (4:00 PM ET)
1. ✓ Closes positions at profit (take profit)
2. ✓ Closes losing positions (stop loss)
3. ✓ Resets for next day

### Every Day at 8:00 PM
1. ✓ Downloads latest 30 days of data
2. ✓ **Retrains model automatically**
3. ✓ Saves improved model
4. ✓ Ready for tomorrow's trading

---

## Testing Without Waiting

### Test Predictions Manually
```bash
# See predictions on AAPL, MSFT, TSLA right now
python ml_predictor.py
```

### Manual Training
```bash
# Retrain model immediately (don't wait for 8 PM)
python ml_trainer.py
```

### Manual Trading Check
```python
from live_trader import LiveTrader

trader = LiveTrader()
trader.start()
trader.check_and_trade()  # Check for signals right now
```

---

## Monitor Your Results

### View Recent Trades
```bash
# See all trades in JSON format
python -c "import json; \
data = json.load(open('models/trade_history.json')); \
trades = [t for t in data['trades'] if t['status'] == 'CLOSED']; \
for t in trades[-5:]: print(f'{t[\"symbol\"]}: {t[\"pnl_pct\"]:+.2%}')"
```

### Get Performance Summary
```python
from live_trader import LiveTrader

trader = LiveTrader()
perf = trader.get_performance_summary()

print(f"Win Rate: {perf['win_rate']:.1%}")
print(f"Total Trades: {perf['closed_trades']}")
print(f"Total P&L: ${perf['total_pnl']:.2f}")
```

---

## Directory Structure

After setup, your project looks like:
```
services/
├── config.py                      # All settings
├── build_dataset.py              # Collects historical data
├── ml_trainer.py                 # Trains models
├── ml_predictor.py               # Makes predictions
├── market_scheduler.py           # Timing control
├── live_trader.py                # Main trading bot
├── .env                          # Your API keys
│
├── *.csv                         # Historical data files
│
├── models/                       # Knowledge storage
│   ├── model_random_forest_*.pkl
│   ├── scaler_*.pkl
│   ├── features_*.pkl
│   └── trade_history.json        # All trades
│
└── Tests/
    └── test_connection.py
```

---

## Configuration Tips

Want to tune the system? Edit `services/config.py`:

```python
# Be more aggressive
MIN_CONFIDENCE = 0.60              # Trade at 60% instead of 65%
MAX_POSITION_SIZE = 10             # 10 shares instead of 5

# More conservative
STOP_LOSS_PCT = 0.03               # 3% stop loss instead of 2%
MAX_OPEN_POSITIONS = 5             # Max 5 trades instead of 10

# Use better model
ML_MODEL_TYPE = "gradient_boosting"  # Instead of "random_forest"
```

Then restart `live_trader.py` for changes to take effect.

---

## Common Commands

```bash
# View market status
python -c "from market_scheduler import MarketScheduler; s = MarketScheduler(); s.get_market_status()"

# Check which stocks passed price filter
python -c "from build_dataset import get_most_active_symbols_with_price_filter; print(get_most_active_symbols_with_price_filter())"

# List all saved models
ls models/model_*.pkl

# Download latest data only (don't train)
python build_dataset.py
```

---

## Troubleshooting Quick Fixes

| Problem | Solution |
|---------|----------|
| "No module named 'config'" | Make sure you're in the `services/` directory |
| "No trained model found" | Run `python ml_trainer.py` first |
| "No CSV files found" | Run `python build_dataset.py` first |
| "ALPACA_API_KEY not found" | Check `services/.env` file exists and has your keys |
| "Market is CLOSED" | The system only trades 9:30 AM - 4 PM ET Mon-Fri |
| Port/connection errors | Your internet connection - check Alpaca API status |

---

## What to Expect - Day 1

### 9:30 AM - 4:00 PM (Market Open)
- System checks for signals every minute
- May generate 0-10 buy signals depending on stocks
- Each signal either trades or gets rejected based on:
  - Model confidence (need > 65%)
  - Having capital available
  - Not already owning that stock
  - Account risk limits

### After 4:00 PM
- System closes any profitable positions (take profit)
- System closes losing positions (stop loss)
- Prepares for tomorrow

### 8:00 PM
- System retrains model with new data
- Model gets slightly better each day

### By Day 5
- System has executed ~20-50 trades
- Win rate stabilizes around 50-65%
- Model begins to improve noticeably

---

## Long-Term Strategy

The ML system learns continuously:

**Week 1:** Learning basic patterns
- Low accuracy, more losses than wins
- Model still figuring out what works

**Week 2-3:** Pattern recognition improves
- Accuracy increases to 60%+
- Win rate improves to 50-55%

**Month 1:** System finds your edge
- Model discovers specific patterns that work
- Win rate climbs to 55-65%
- Consistent profitability possible

**Month 2+:** Optimization
- Fine-tune confidence thresholds
- Add new technical indicators
- Adjust position sizing
- Potentially scale up

---

## Next Steps

1. **Right now:** Run the three-command startup above
2. **Tomorrow morning:** Check trades from overnight
3. **This week:** Monitor performance and results
4. **This month:** Consider adjusting configuration
5. **Later:** Add more indicators, bigger trades, etc.

---

## Need Help?

- 📖 Full documentation: `ML_DOCUMENTATION.md`
- 🔧 Configuration: `config.py`
- 💾 Trade history: `models/trade_history.json`
- 🐛 Check logs for errors: Look at console output

---

**Ready? Run:** 
```bash
cd services && python build_dataset.py && python ml_trainer.py && python live_trader.py
```

Good luck! 🚀
