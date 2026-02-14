# ml_predictor.py
# Real-time predictions using trained models
# Makes trading signals during market hours

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from config import *
from ml_trainer import MLTrainer


class MLPredictor:
    """
    Uses trained models to make real-time predictions on new market data.
    Stores confidence scores and prediction history.
    Supports multiple trading strategies.
    """
    
    def __init__(self, strategy='macd_crossover'):
        self.strategy = strategy
        self.model = None
        self.scaler = None
        self.feature_columns = None
        self.trainer = MLTrainer()
        self.prediction_history = {}  # Store recent predictions
        
        # Load latest trained model for this strategy
        self._load_model()
    
    def _load_model(self):
        """Load the most recent trained model for the strategy"""
        model, scaler, features = self.trainer.load_latest_model(
            ML_MODEL_TYPE, 
            strategy=self.strategy
        )
        
        if model is None:
            logger.warning(f"No trained model found for {self.strategy}. Run ml_trainer.py first!")
            self.model = None
            return False
        
        self.model = model
        self.scaler = scaler
        self.feature_columns = features
        logger.info(f"Model loaded for {self.strategy} and ready for predictions")
        return True
    
    def is_model_ready(self):
        """Check if model is loaded and ready"""
        return self.model is not None and self.scaler is not None
    
    def fetch_current_bars(self, symbol, lookback_bars=20):
        """Fetch recent bars for a symbol"""
        try:
            params = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=TimeFrame.Minute,
                limit=lookback_bars
            )
            bars = data_client.get_stock_bars(params)
            
            if not bars or symbol not in bars:
                return None
            
            bar_data = bars[symbol]
            if len(bar_data) == 0:
                return None
            
            # Convert to DataFrame
            data = []
            for bar in bar_data:
                data.append({
                    'timestamp': bar.timestamp,
                    'open': bar.open,
                    'high': bar.high,
                    'low': bar.low,
                    'close': bar.close,
                    'volume': bar.volume
                })
            
            df = pd.DataFrame(data)
            df.set_index('timestamp', inplace=True)
            return df
        
        except Exception as e:
            logger.warning(f"Failed to fetch bars for {symbol}: {e}")
            return None
    
    def engineer_features(self, df):
        """Calculate technical indicators on recent bars"""
        if df is None or len(df) < 5:
            return None
        
        try:
            # Rename columns to match training data
            df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            
            # VWAP
            df['Typical_Price'] = (df['High'] + df['Low'] + df['Close']) / 3
            df['TP_Volume'] = df['Typical_Price'] * df['Volume']
            df['Cum_TP_Volume'] = df['TP_Volume'].cumsum()
            df['Cum_Volume'] = df['Volume'].cumsum()
            df['VWAP'] = df['Cum_TP_Volume'] / df['Cum_Volume']
            
            # MACD
            if TALIB_AVAILABLE:
                macd, signal, hist = talib.MACD(df['Close'].values)
                df['MACD'] = macd
                df['MACD_Signal'] = signal
                df['MACD_Hist'] = hist
            else:
                ema_fast = df['Close'].ewm(span=12, adjust=False).mean()
                ema_slow = df['Close'].ewm(span=26, adjust=False).mean()
                macd = ema_fast - ema_slow
                signal = macd.ewm(span=9, adjust=False).mean()
                df['MACD'] = macd
                df['MACD_Signal'] = signal
                df['MACD_Hist'] = macd - signal
            
            df['VWAP_Deviation'] = (df['Close'] - df['VWAP']) / df['VWAP']
            
            return df.dropna()
        
        except Exception as e:
            logger.error(f"Feature engineering failed: {e}")
            return None
    
    def predict(self, symbol, lookback_bars=20):
        """
        Make a prediction for a symbol.
        
        Returns:
            dict with keys:
                - "signal": 0 or 1 (1 = buy signal)
                - "confidence": probability of buy signal (0-1)
                - "price": current price
                - "recommendation": "BUY" or "HOLD"
        """
        if not self.is_model_ready():
            logger.warning("Model not ready for predictions")
            return None
        
        try:
            # Fetch recent bars
            df = self.fetch_current_bars(symbol, lookback_bars)
            if df is None or len(df) < 5:
                return None
            
            # Engineer features
            df = self.engineer_features(df)
            if df is None:
                return None
            
            # Use latest row for prediction
            latest = df.iloc[-1]
            X = latest[self.feature_columns].values.reshape(1, -1)
            
            # Scale
            X_scaled = self.scaler.transform(X)
            
            # Predict
            signal = self.model.predict(X_scaled)[0]
            confidence = self.model.predict_proba(X_scaled)[0]
            
            # Get confidence for the predicted class
            if signal == 1:
                confidence_score = confidence[1]
            else:
                confidence_score = confidence[0]
            
            current_price = latest['Close']
            
            # Decision
            meets_threshold = confidence_score >= MIN_CONFIDENCE
            recommendation = "BUY" if (signal == 1 and meets_threshold) else "HOLD"
            
            result = {
                "symbol": symbol,
                "signal": int(signal),
                "confidence": float(confidence_score),
                "confidence_high": float(max(confidence)),
                "price": float(current_price),
                "recommendation": recommendation,
                "meets_threshold": meets_threshold,
                "timestamp": datetime.now(TIMEZONE)
            }
            
            # Store in history
            if symbol not in self.prediction_history:
                self.prediction_history[symbol] = []
            self.prediction_history[symbol].append(result)
            
            # Keep only last 100 predictions per symbol
            if len(self.prediction_history[symbol]) > 100:
                self.prediction_history[symbol] = self.prediction_history[symbol][-100:]
            
            return result
        
        except Exception as e:
            logger.error(f"Prediction failed for {symbol}: {e}")
            return None
    
    def get_buy_signals(self, symbols):
        """
        Get all buy signals across multiple symbols
        
        Returns: list of symbols with BUY recommendations
        """
        buy_signals = []
        
        for symbol in symbols:
            result = self.predict(symbol)
            if result and result['recommendation'] == "BUY":
                buy_signals.append(result)
                logger.info(
                    f"BUY SIGNAL: {symbol} @ ${result['price']:.2f} "
                    f"(confidence: {result['confidence']:.2%})"
                )
        
        return buy_signals
    
    def get_prediction_history(self, symbol=None):
        """Get prediction history for analysis"""
        if symbol:
            return self.prediction_history.get(symbol, [])
        return self.prediction_history


if __name__ == "__main__":
    # Test the predictor
    predictor = MLPredictor()
    
    if predictor.is_model_ready():
        logger.info("\nTesting predictions on sample stocks...")
        test_symbols = ["AAPL", "MSFT", "TSLA"]
        
        for sym in test_symbols:
            result = predictor.predict(sym)
            if result:
                logger.info(f"\n{sym}:")
                logger.info(f"  Price: ${result['price']:.2f}")
                logger.info(f"  Signal: {result['signal']}")
                logger.info(f"  Confidence: {result['confidence']:.2%}")
                logger.info(f"  Recommendation: {result['recommendation']}")
    else:
        logger.error("Model not ready. Train a model first with ml_trainer.py")
        sys.exit(1)
