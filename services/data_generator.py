import numpy as np
import time
from collections import deque

class MarketDataGenerator:
    def __init__(self, symbols=None):
        self.symbols = symbols or ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]
        self.base_prices = {
            "AAPL": 178.50,
            "GOOGL": 141.80,
            "MSFT": 378.90,
            "AMZN": 178.25,
            "TSLA": 248.50
        }
        self.current_prices = dict(self.base_prices)
        self.price_history = {s: deque(maxlen=200) for s in self.symbols}
        self.volume_history = {s: deque(maxlen=200) for s in self.symbols}
        self.tick_count = 0
        self._initialize_history()

    def _initialize_history(self):
        for symbol in self.symbols:
            price = self.base_prices[symbol]
            for i in range(100):
                change = np.random.normal(0, price * 0.002)
                price = max(price * 0.9, price + change)
                self.price_history[symbol].append(price)
                self.volume_history[symbol].append(int(np.random.uniform(100000, 5000000)))
            self.current_prices[symbol] = price

    def generate_tick(self):
        self.tick_count += 1
        ticks = []
        for symbol in self.symbols:
            price = self.current_prices[symbol]
            volatility = price * 0.001
            change = np.random.normal(0, volatility)
            momentum = 0.0
            if len(self.price_history[symbol]) >= 5:
                recent = list(self.price_history[symbol])[-5:]
                momentum = (recent[-1] - recent[0]) / recent[0] * 0.1

            new_price = round(price + change + momentum * price, 2)
            new_price = max(new_price, price * 0.95)
            new_price = min(new_price, price * 1.05)

            volume = int(np.random.uniform(100000, 5000000))
            spread = round(new_price * 0.0005, 2)

            self.current_prices[symbol] = new_price
            self.price_history[symbol].append(new_price)
            self.volume_history[symbol].append(volume)

            ticks.append({
                "symbol": symbol,
                "price": new_price,
                "change": round(new_price - price, 2),
                "change_pct": round((new_price - price) / price * 100, 4),
                "volume": volume,
                "bid": round(new_price - spread, 2),
                "ask": round(new_price + spread, 2),
                "timestamp": time.time()
            })
        return ticks

    def get_history(self, symbol, points=100):
        if symbol not in self.price_history:
            return []
        prices = list(self.price_history[symbol])[-points:]
        volumes = list(self.volume_history[symbol])[-points:]
        return [{"price": p, "volume": v, "index": i} for i, (p, v) in enumerate(zip(prices, volumes))]

    def get_all_current(self):
        return {s: {"price": self.current_prices[s], "base": self.base_prices[s]} for s in self.symbols}
