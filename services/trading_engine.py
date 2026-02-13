import time
from collections import deque

class TradingEngine:
    def __init__(self):
        self.portfolio = {
            "cash": 100000.00,
            "positions": {},
            "total_value": 100000.00
        }
        self.trades = deque(maxlen=50)
        self.pnl_history = deque(maxlen=200)
        self.trade_count = 0

    def execute_signal(self, symbol, signal, price, confidence):
        if confidence < 30:
            return None

        trade = None
        position = self.portfolio["positions"].get(symbol, {"qty": 0, "avg_price": 0})

        if signal == "BUY" and self.portfolio["cash"] >= price * 10:
            qty = min(int(self.portfolio["cash"] * 0.1 / price), 100)
            if qty > 0:
                cost = qty * price
                self.portfolio["cash"] -= cost
                new_qty = position["qty"] + qty
                if new_qty > 0:
                    new_avg = (position["avg_price"] * position["qty"] + cost) / new_qty
                else:
                    new_avg = price
                self.portfolio["positions"][symbol] = {"qty": new_qty, "avg_price": round(new_avg, 2)}
                trade = {"action": "BUY", "symbol": symbol, "qty": qty, "price": price, "timestamp": time.time()}

        elif signal == "SELL" and position["qty"] > 0:
            qty = min(position["qty"], 50)
            revenue = qty * price
            self.portfolio["cash"] += revenue
            pnl = (price - position["avg_price"]) * qty
            remaining = position["qty"] - qty
            if remaining > 0:
                self.portfolio["positions"][symbol] = {"qty": remaining, "avg_price": position["avg_price"]}
            else:
                self.portfolio["positions"].pop(symbol, None)
            trade = {"action": "SELL", "symbol": symbol, "qty": qty, "price": price, "pnl": round(pnl, 2), "timestamp": time.time()}

        if trade:
            self.trade_count += 1
            trade["id"] = self.trade_count
            self.trades.appendleft(trade)

        return trade

    def get_portfolio_value(self, current_prices):
        positions_value = sum(
            data["qty"] * current_prices.get(sym, {}).get("price", data["avg_price"])
            for sym, data in self.portfolio["positions"].items()
        )
        self.portfolio["total_value"] = round(self.portfolio["cash"] + positions_value, 2)
        self.pnl_history.append(self.portfolio["total_value"])
        return {
            "cash": round(self.portfolio["cash"], 2),
            "positions_value": round(positions_value, 2),
            "total_value": self.portfolio["total_value"],
            "pnl": round(self.portfolio["total_value"] - 100000, 2),
            "pnl_pct": round((self.portfolio["total_value"] - 100000) / 100000 * 100, 2),
            "positions": dict(self.portfolio["positions"])
        }

    def get_recent_trades(self, limit=20):
        return list(self.trades)[:limit]

    def get_pnl_history(self):
        return list(self.pnl_history)
