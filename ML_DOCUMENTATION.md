# Machine Learning Trading System Documentation

Your algorithmic trading application now has a complete ML-powered trading system that:
- **Learns from historical data** during market-closed hours
- **Actively paper trades** during market hours using ML predictions
- **Stores all knowledge** in persistent model files and trade logs
- **Auto-retrains daily** with new market data for continuous improvement

---

## System Architecture

### 1. **ml_trainer.py** - Model Training Pipeline
Trains machine learning models on historical market data.

**What it does:**
- Loads historical stock data (from `build_dataset.py`)
- Engineers technical features (VWAP, MACD, price deviations)
- Trains RandomForest or GradientBoosting models
- Evaluates performance with classification metrics
- Saves trained models for real-time use

**Usage:**
```bash
python ml_trainer.py
```

**Output:**
- `models/model_random_forest_YYYYMMDD_HHMMSS.pkl` - Trained model
- `models/scaler_YYYYMMDD_HHMMSS.pkl` - Feature scaler
- `models/features_YYYYMMDD_HHMMSS.pkl` - Feature column names

---

### 2. **ml_predictor.py** - Real-Time Predictions
Makes trading signals on live market data using trained models.

**What it does:**
- Loads the most recent trained model
- Fetches live market bars for stocks
- Calculates features on latest data
- Predicts buy/sell signals with confidence scores
- Maintains prediction history for analysis

**Usage (testing):**
```bash
python ml_predictor.py
```

**Key Methods:**
```python
from ml_predictor import MLPredictor

predictor = MLPredictor()

# Single prediction
result = predictor.predict("AAPL")
# Returns: {
#   'symbol': 'AAPL',
#   'signal': 1,  # 1 = buy, 0 = hold
#   'confidence': 0.78,
#   'price': 150.50,
#   'recommendation': 'BUY',
#   'meets_threshold': True
# }

# Multiple predictions
buy_signals = predictor.get_buy_signals(["AAPL", "MSFT", "TSLA"])
```

---

### 3. **market_scheduler.py** - Market Hours Management
Handles timing and scheduling of all trading activities.

**What it does:**
- Detects if US stock market is currently open
- Schedules daily training at 8 PM ET (after market close)
- Schedules portfolio rebalancing at 4 AM ET (before market open)
- Runs live trading checks every minute during market hours
- Prevents trading during closed markets

**Market Hours:**
- **Open:** 9:30 AM - 4:00 PM ET (Monday-Friday)
- **Training:** 8:00 PM ET (daily)
- **Rebalance:** 4:00 AM ET (daily)

---

### 4. **live_trader.py** - Main Trading Orchestrator
The central hub that ties everything together and executes real trades.

**What it does:**
- Monitors market during trading hours
- Generates buy signals using ML predictions
- Executes paper trades via Alpaca API
- Manages positions with risk controls
- Rebalances positions based on stop loss/take profit
- Stores all decisions and outcomes for learning

**Risk Management:**
- Max position size: 5 shares
- Max open positions: 10
- Stop loss: 2% per trade
- Take profit: 4% per trade
- Position sizing: 1% account equity risk per trade

**Usage:**
```bash
python live_trader.py
```

---

## Workflow & Knowledge Storage

### Daily Training Cycle (Automated)

```
┌─────────────────────────────────────────────────┐
│ 8:00 PM ET: Market Closed - Training Time     │
├─────────────────────────────────────────────────┤
│ 1. Fetch new historical data (past 30 days)   │
│ 2. Engineer technical indicators              │
│ 3. Train ML model on latest data              │
│ 4. Evaluate model performance                 │
│ 5. Save model (stores knowledge gained)       │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│ 4:00 AM ET: Pre-Market Rebalancing            │
├─────────────────────────────────────────────────┤
│ 1. Close losing positions (stop loss)         │
│ 2. Close winning positions (take profit)      │
│ 3. Ready for new signals                      │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│ 9:30 AM - 4:00 PM ET: Active Trading          │
├─────────────────────────────────────────────────┤
│ Every minute:                                 │
│ 1. Get list of active stocks                  │
│ 2. Run ML predictions                         │
│ 3. Execute BUY orders on high-confidence      │
│    signals                                    │
│ 4. Log all signals and trades                 │
│                                               │
│ Continuous position monitoring:               │
│ - Track PnL                                   │
│ - Enforce stop loss/take profit               │
│ - Manage risk                                 │
└─────────────────────────────────────────────────┘
```

### Knowledge Storage

All learned information is stored in the `models/` directory:

```
models/
├── model_random_forest_20260214_203015.pkl     # Trained ML model
├── scaler_20260214_203015.pkl                   # Feature scaling
├── features_20260214_203015.pkl                 # Feature names
├── trade_history.json                           # All trades & signals
└── ...
```

**trade_history.json example:**
```json
{
  "trades": [
    {
      "symbol": "AAPL",
      "side": "BUY",
      "qty": 3,
      "price": 150.50,
      "confidence": 0.78,
      "entry_time": "2026-02-14T10:35:00-05:00",
      "stop_loss": 147.49,
      "take_profit": 156.52,
      "status": "CLOSED",
      "exit_price": 154.25,
      "exit_time": "2026-02-14T14:20:00-05:00",
      "pnl_pct": 0.0249,
      "pnl_amount": 11.25
    }
  ],
  "signals": [
    {
      "symbol": "MSFT",
      "price": 380.25,
      "confidence": 0.71,
      "timestamp": "2026-02-14T10:30:00-05:00"
    }
  ]
}
```

---

## Getting Started

### Step 1: Generate Training Data
```bash
python build_dataset.py
```
This collects 30 days of historical data for active stocks.

### Step 2: Train Your First Model
```bash
python ml_trainer.py
```
Output shows:
- Feature importances
- Model accuracy
- Precision/Recall metrics
- Saved model location

### Step 3: Test Predictions (Optional)
```bash
python ml_predictor.py
```
Shows sample predictions on AAPL, MSFT, TSLA.

### Step 4: Start Live Trading
```bash
python live_trader.py
```

The system will:
- Load your trained model
- Wait for market open (9:30 AM ET)
- Automatically check for signals every minute
- Execute paper trades based on ML predictions
- Auto-train daily at 8 PM
- Auto-rebalance daily at 4 AM

---

## Configuration

Edit `config.py` to tune the system:

```python
# Model Configuration
ML_MODEL_TYPE = "random_forest"      # or "gradient_boosting"
MIN_CONFIDENCE = 0.65                # Only trade signals > 65% confidence
MIN_TRAINING_SAMPLES = 500           # Minimum data points to train

# Risk Management
MAX_POSITION_SIZE = 5                # Max 5 shares per trade
MAX_OPEN_POSITIONS = 10              # Never more than 10 open trades
STOP_LOSS_PCT = 0.02                 # 2% stop loss
TAKE_PROFIT_PCT = 0.04               # 4% take profit

# Scheduling
TRAIN_TIME = "20:00"                 # 8 PM daily training
REBALANCE_TIME = "04:00"             # 4 AM daily rebalancing
```

---

## Monitoring Performance

### View Recent Predictions
```python
from ml_predictor import MLPredictor

predictor = MLPredictor()
history = predictor.get_prediction_history("AAPL")
for pred in history[-5:]:  # Last 5 predictions
    print(f"{pred['symbol']}: {pred['recommendation']} @ ${pred['price']:.2f}")
```

### View Trade Performance
```python
from live_trader import LiveTrader

trader = LiveTrader()
summary = trader.get_performance_summary()
print(f"Win Rate: {summary['win_rate']:.2%}")
print(f"Total P&L: ${summary['total_pnl']:.2f}")
print(f"Closed Trades: {summary['closed_trades']}")
```

### Analyze Trade Logs
```python
import json

with open("models/trade_history.json", 'r') as f:
    data = json.load(f)
    
closed_trades = [t for t in data['trades'] if t['status'] == 'CLOSED']
avg_win = sum(t['pnl_pct'] for t in closed_trades if t['pnl_pct'] > 0) / len([t for t in closed_trades if t['pnl_pct'] > 0])
avg_loss = sum(t['pnl_pct'] for t in closed_trades if t['pnl_pct'] <= 0) / len([t for t in closed_trades if t['pnl_pct'] <= 0])

print(f"Average Win: {avg_win:.2%}")
print(f"Average Loss: {avg_loss:.2%}")
print(f"Profit Factor: {abs(avg_win / avg_loss):.2f}")
```

---

## How It Learns Over Time

1. **Every Day After 8 PM:**
   - New historical data is downloaded
   - Model is retrained with the latest 30 days
   - Old knowledge is discarded, new patterns are learned
   - Model performance is evaluated

2. **Trade Outcomes Record:**
   - Every trade is logged with entry price, confidence, exit price, and P&L
   - Over time, the model learns which signals lead to profitable trades
   - Failed signals help the model improve

3. **Feature Evolution:**
   - The model identifies which technical indicators matter most
   - Feature importances are saved for analysis
   - Weak features can be removed in future versions

4. **Continuous Improvement:**
   - As more historical data accumulates, the model becomes more robust
   - The system adapts to changing market conditions daily
   - Position sizing adjusts based on account equity

---

## Troubleshooting

### "No trained model found"
**Solution:** Run `python ml_trainer.py` first to train a model.

### "Insufficient training data"
**Solution:** Run `python build_dataset.py` to collect more historical data.

### "Model not ready for predictions"
**Solution:** Ensure the model file exists in `models/` directory.

### "No buy signals generated"
**Solution:** 
- Check `MIN_CONFIDENCE` threshold - lower it to 0.60
- Verify market is open (9:30 AM - 4:00 PM ET)
- Check that stocks have enough volume

### Why aren't trades being executed?
**Possible reasons:**
1. Market is closed (trading only 9:30 AM - 4:00 PM ET)
2. Not enough buying power (check account balance)
3. No high-confidence signals generated
4. Already have position in that stock

---

## Performance Tips

1. **Increase Training Data:** Use 60+ days instead of 30
   - Edit `DAYS_BACK = 60` in config.py before running build_dataset.py

2. **Lower Confidence Threshold:** Trade on more signals
   - Edit `MIN_CONFIDENCE = 0.60` for 60% instead of 65%

3. **Better Features:** Add momentum indicators in build_dataset.py
   - RSI, Bollinger Bands, ATR, etc.

4. **Larger Risk Budget:** Risk more per trade (carefully!)
   - Edit position sizing logic for higher P&L potential

5. **Different Model:** Try GradientBoosting
   - Change `ML_MODEL_TYPE = "gradient_boosting"` in config.py

---

## Next Steps

Now that your ML system is set up:

1. ✅ Run data collection: `python build_dataset.py`
2. ✅ Train model: `python ml_trainer.py`
3. ✅ Start trading: `python live_trader.py`
4. 📊 Monitor performance daily
5. 🔄 Retrain model with new data (automatic at 8 PM)
6. 📈 Analyze what works and iterate

The more data you collect and the more trades you make, the smarter your system becomes!
