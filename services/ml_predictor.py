import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures

class TradingPredictor:
    def __init__(self):
        self.models = {}

    def predict(self, price_history, steps_ahead=10):
        if len(price_history) < 20:
            return {"prediction": [], "signal": "HOLD", "confidence": 0}

        prices = np.array([p["price"] for p in price_history])
        X = np.arange(len(prices)).reshape(-1, 1)
        y = prices

        poly = PolynomialFeatures(degree=2)
        X_poly = poly.fit_transform(X)

        model = LinearRegression()
        model.fit(X_poly, y)

        future_X = np.arange(len(prices), len(prices) + steps_ahead).reshape(-1, 1)
        future_X_poly = poly.transform(future_X)
        predictions = model.predict(future_X_poly).tolist()

        train_pred = model.predict(X_poly)
        ss_res = np.sum((y - train_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = max(0, 1 - ss_res / ss_tot) if ss_tot > 0 else 0

        current_price = prices[-1]
        predicted_price = predictions[-1]
        price_change_pct = (predicted_price - current_price) / current_price * 100

        if price_change_pct > 0.15:
            signal = "BUY"
        elif price_change_pct < -0.15:
            signal = "SELL"
        else:
            signal = "HOLD"

        sma_5 = np.mean(prices[-5:])
        sma_20 = np.mean(prices[-20:]) if len(prices) >= 20 else sma_5
        rsi = self._compute_rsi(prices)
        volatility = np.std(prices[-20:]) / np.mean(prices[-20:]) * 100

        return {
            "prediction": [round(p, 2) for p in predictions],
            "signal": signal,
            "confidence": round(r_squared * 100, 1),
            "price_change_pct": round(price_change_pct, 4),
            "indicators": {
                "sma_5": round(sma_5, 2),
                "sma_20": round(sma_20, 2),
                "rsi": round(rsi, 1),
                "volatility": round(volatility, 4)
            }
        }

    def _compute_rsi(self, prices, period=14):
        if len(prices) < period + 1:
            return 50.0
        deltas = np.diff(prices[-(period + 1):])
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        avg_gain = np.mean(gains)
        avg_loss = np.mean(losses)
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
