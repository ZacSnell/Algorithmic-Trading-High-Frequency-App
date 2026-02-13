# Algorithmic Trading High-Frequency App

## Overview
A real-time algorithmic trading simulation dashboard with ML-powered predictions. The app simulates high-frequency trading across 5 major stocks (AAPL, GOOGL, MSFT, AMZN, TSLA) using synthetic market data, machine learning price predictions, and an automated trading engine.

## Project Architecture
- **Backend**: Python/Flask serving on 0.0.0.0:5000
- **Frontend**: Vanilla HTML/CSS/JS with Chart.js (CDN) for charting
- **ML**: scikit-learn polynomial regression for price prediction + RSI/SMA indicators
- **Data**: Synthetic market data generator (no external APIs needed)

## File Structure
```
app.py                  - Flask application entry point
services/
  data_generator.py     - Synthetic market data generation
  ml_predictor.py       - ML price prediction (sklearn)
  trading_engine.py     - Automated trading engine with portfolio management
templates/
  index.html            - Dashboard HTML template
static/
  css/style.css         - Dashboard styling
  js/app.js             - Frontend logic, charts, polling
```

## API Endpoints
- `GET /` - Dashboard page
- `GET /api/tick` - Generate new market tick + predictions + trades
- `GET /api/history/<symbol>` - Price history + prediction for a symbol
- `GET /api/portfolio` - Current portfolio state
- `GET /api/pnl` - P&L history

## Key Features
- Live market data simulation with realistic price movements
- ML-based trading signals (BUY/SELL/HOLD) with confidence scores
- Automated trade execution based on signals
- Portfolio tracking with P&L
- Interactive price charts with prediction overlay
- Technical indicators (RSI, SMA, Volatility)

## Running
```
python app.py
```
Runs on port 5000.
