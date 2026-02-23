# services/live_trader.py - FINAL 7-AGENT VERSION
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from config import *
from ml_ensemble import EnsembleCoordinator
from ml_trainer import MLTrainer
from market_scheduler import MarketScheduler
from build_dataset import get_most_active_symbols_with_price_filter, add_features_and_target
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime, timedelta
import json
import time

class LiveTrader:
    def __init__(self):
        self.predictor = EnsembleCoordinator()   # 7-AGENT ENSEMBLE
        self.trainer = MLTrainer()
        self.scheduler = MarketScheduler(
            training_callback=self.scheduled_training,
            trading_callback=self.check_and_trade,
            rebalance_callback=self.rebalance_portfolio
        )

        self.positions = {}
        self.trade_log = []
        self.signals_log = []
        self.load_trade_history()

    def load_trade_history(self):
        history_file = MODELS_DIR / "trade_history.json"
        if history_file.exists():
            try:
                with open(history_file, 'r') as f:
                    data = json.load(f)
                    self.trade_log = data.get('trades', [])
                    self.signals_log = data.get('signals', [])
                logger.info(f"Loaded {len(self.trade_log)} previous trades")
            except Exception as e:
                logger.warning(f"Could not load trade history: {e}")

    def save_trade_history(self):
        history_file = MODELS_DIR / "trade_history.json"
        try:
            data = {
                'trades': self.trade_log[-1000:],
                'signals': self.signals_log[-5000:],
                'saved_at': datetime.now(TIMEZONE).isoformat()
            }
            with open(history_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save trade history: {e}")

    def get_open_positions(self):
        try:
            positions = trade_client.get_all_positions()
            return {pos.symbol: pos for pos in positions}
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            return {}

    def get_account_info(self):
        try:
            account = trade_client.get_account()
            return {
                'buying_power': float(account.buying_power),
                'portfolio_value': float(account.portfolio_value),
                'equity': float(account.equity),
                'cash': float(account.cash)
            }
        except Exception as e:
            logger.error(f"Failed to get account info: {e}")
            return None

    def can_open_position(self, symbol):
        positions = self.get_open_positions()
        if symbol in positions:
            return False, "Already have open position"
        if len(positions) >= MAX_OPEN_POSITIONS:
            return False, f"Max open positions ({MAX_OPEN_POSITIONS}) reached"
        account = self.get_account_info()
        if not account or account['buying_power'] < 100:
            return False, "Insufficient buying power"
        return True, "Ready to trade"

    def _get_and_engineer_features(self, symbol):
        try:
            request_params = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=TimeFrame.Minute,
                start=(datetime.now(TIMEZONE) - timedelta(days=5)).date(),
                limit=500
            )
            bars = data_client.get_stock_bars(request_params).df
            if bars.empty:
                return None
            df = bars.reset_index()
            df = df.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume', 'timestamp': 'timestamp'})
            df = df.set_index('timestamp')
            df = add_features_and_target(df)
            return df
        except Exception as e:
            logger.warning(f"Could not fetch features for {symbol}: {e}")
            return None

    def submit_order(self, symbol, qty, side):
        try:
            from alpaca.trading.requests import MarketOrderRequest
            from alpaca.trading.enums import OrderSide, TimeInForce
            order_side = OrderSide.BUY if side == "buy" else OrderSide.SELL
            order_data = MarketOrderRequest(symbol=symbol, qty=qty, side=order_side, time_in_force=TimeInForce.DAY)
            order = trade_client.submit_order(order_data)
            logger.info(f"Order submitted: {side.upper()} {qty} {symbol}")
            return order
        except Exception as e:
            logger.error(f"Order submission failed: {e}")
            return None

    def check_and_trade(self):
        try:
            candidates = get_most_active_symbols_with_price_filter()
            buy_signals = []
            for symbol in candidates[:15]:
                features_df = self._get_and_engineer_features(symbol)
                if features_df is None or len(features_df) < 50:
                    continue
                result = self.predictor.predict(features_df, symbol)
                if result.get('recommendation') == "BUY":
                    buy_signals.append({
                        'symbol': symbol,
                        'price': features_df['Close'].iloc[-1],
                        'confidence': result['confidence']
                    })
            for signal in buy_signals:
                symbol = signal['symbol']
                price = signal['price']
                can_trade, reason = self.can_open_position(symbol)
                if not can_trade:
                    continue
                account = self.get_account_info()
                position_value = account['buying_power'] * (POSITION_SIZE_PCT / 100.0)
                qty = int(position_value / price)
                if qty < 1:
                    continue
                order = self.submit_order(symbol, qty, "buy")
                if order:
                    trade_record = {
                        'symbol': symbol,
                        'side': 'BUY',
                        'qty': qty,
                        'price': price,
                        'confidence': signal['confidence'],
                        'entry_time': datetime.now(TIMEZONE).isoformat(),
                        'stop_loss': price * (1 - STOP_LOSS_PCT),
                        'take_profit': price * (1 + TAKE_PROFIT_PCT),
                        'status': 'OPEN'
                    }
                    self.trade_log.append(trade_record)
                    logger.info(f"TRADE EXECUTED: {symbol} BUY {qty} @ ${price:.2f}")
        except Exception as e:
            logger.error(f"Trading check failed: {e}")

    def rebalance_portfolio(self):
        try:
            positions = self.get_open_positions()
            for symbol, position in positions.items():
                current_price = float(position.current_price)
                entry_price = float(position.avg_fill_price)
                qty = float(position.qty)
                pnl_pct = (current_price - entry_price) / entry_price if entry_price > 0 else 0
                if pnl_pct <= -STOP_LOSS_PCT or pnl_pct >= TAKE_PROFIT_PCT:
                    self.submit_order(symbol, qty, "sell")
        except Exception as e:
            logger.error(f"Rebalancing failed: {e}")

    def scheduled_training(self):
        try:
            self.trainer.train_all_specialists()
            self.predictor = EnsembleCoordinator()  # Reload fresh ensemble
        except Exception as e:
            logger.error(f"Scheduled training failed: {e}")

    def start(self):
        logger.info("\n" + "="*60)
        logger.info("STARTING LIVE TRADING SYSTEM - 7-AGENT ENSEMBLE ACTIVE")
        logger.info("="*60)
        self.scheduler.start()
        logger.info("Live trading system started successfully")
        return True

    def stop(self):
        logger.info("Stopping live trading system...")
        self.scheduler.stop()
        self.save_trade_history()

def main():
    trader = LiveTrader()
    try:
        if trader.start():
            logger.info("\nTrading system running. Press Ctrl+C to stop...")
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        logger.info("\nShutting down...")
        trader.stop()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        trader.stop()

if __name__ == "__main__":
    main()