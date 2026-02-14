# live_trader.py
# Main orchestrator for live paper trading
# Executes trades based on ML predictions during market hours

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from config import *
from ml_predictor import MLPredictor
from ml_trainer import MLTrainer
from market_scheduler import MarketScheduler
from build_dataset import get_most_active_symbols_with_price_filter
from datetime import datetime, timedelta
import json


class LiveTrader:
    """
    Main trading orchestrator.
    - Monitors market for signals using ML predictions
    - Executes paper trades via Alpaca API
    - Manages positions and risk
    - Stores all decisions and outcomes for learning
    """
    
    def __init__(self):
        self.predictor = MLPredictor()
        self.trainer = MLTrainer()
        self.scheduler = MarketScheduler(
            training_callback=self.scheduled_training,
            trading_callback=self.check_and_trade,
            rebalance_callback=self.rebalance_portfolio
        )
        
        self.positions = {}  # Track open positions
        self.trade_log = []  # Log all trades
        self.signals_log = []  # Log all signals
        self.load_trade_history()
    
    def load_trade_history(self):
        """Load previous trading history and positions"""
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
        """Save all trades and signals to file"""
        history_file = MODELS_DIR / "trade_history.json"
        
        try:
            data = {
                'trades': self.trade_log[-1000:],  # Keep last 1000 trades
                'signals': self.signals_log[-5000:],  # Keep last 5000 signals
                'saved_at': datetime.now(TIMEZONE).isoformat()
            }
            
            with open(history_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save trade history: {e}")
    
    def get_open_positions(self):
        """Get current open positions from Alpaca"""
        try:
            positions = trade_client.get_all_positions()
            return {pos.symbol: pos for pos in positions}
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            return {}
    
    def get_account_info(self):
        """Get current account info"""
        try:
            account = trade_client.get_account()
            return {
                'buying_power': float(account.buying_power),
                'portfolio_value': float(account.portfolio_value),
                'equity': float(account.equity),
                'cash': float(account.cash),
                'buying_power_multiplier': float(account.multiplier)
            }
        except Exception as e:
            logger.error(f"Failed to get account info: {e}")
            return None
    
    def can_open_position(self, symbol, max_position_size=MAX_POSITION_SIZE):
        """Check if we can open a new position"""
        positions = self.get_open_positions()
        
        # Already have position in this symbol
        if symbol in positions:
            return False, "Already have open position"
        
        # Too many open positions
        if len(positions) >= MAX_OPEN_POSITIONS:
            return False, f"Max open positions ({MAX_OPEN_POSITIONS}) reached"
        
        account = self.get_account_info()
        if not account:
            return False, "Could not get account info"
        
        # Enough buying power
        required_capital = max_position_size * 100  # Rough estimate
        if account['buying_power'] < required_capital:
            return False, f"Insufficient buying power (${account['buying_power']:.2f})"
        
        return True, "Ready to trade"
    
    def submit_order(self, symbol, qty, side, price=None):
        """Submit an order to Alpaca"""
        try:
            from alpaca.trading.requests import MarketOrderRequest
            from alpaca.trading.enums import OrderSide, TimeInForce
            
            order_side = OrderSide.BUY if side == "buy" else OrderSide.SELL
            
            order_data = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=order_side,
                time_in_force=TimeInForce.DAY
            )
            
            order = trade_client.submit_order(order_data)
            
            logger.info(f"Order submitted: {side.upper()} {qty} {symbol} @ market")
            return order
        
        except Exception as e:
            logger.error(f"Order submission failed: {e}")
            return None
    
    def check_and_trade(self):
        """Main trading function - runs every minute during market hours"""
        try:
            # Get trading candidates
            candidates = get_most_active_symbols_with_price_filter()
            if not candidates:
                return
            
            # Get buy signals
            buy_signals = self.predictor.get_buy_signals(candidates)
            
            # Log signals
            for signal in buy_signals:
                self.signals_log.append({
                    'symbol': signal['symbol'],
                    'price': signal['price'],
                    'confidence': signal['confidence'],
                    'timestamp': signal['timestamp'].isoformat()
                })
            
            if not buy_signals:
                return
            
            logger.info(f"\nFound {len(buy_signals)} buy signals")
            
            # Process each buy signal
            for signal in buy_signals:
                symbol = signal['symbol']
                price = signal['price']
                confidence = signal['confidence']
                
                # Check if we can open position
                can_trade, reason = self.can_open_position(symbol)
                if not can_trade:
                    logger.info(f"Cannot trade {symbol}: {reason}")
                    continue
                
                # Calculate position size (risk-based)
                account = self.get_account_info()
                risk_amount = account['equity'] * 0.01  # Risk 1% per trade
                qty = int(risk_amount / price)
                
                if qty < 1:
                    logger.warning(f"Position size too small for {symbol}")
                    continue
                
                qty = min(qty, MAX_POSITION_SIZE)
                
                # Submit order
                order = self.submit_order(symbol, qty, "buy")
                
                if order:
                    trade_record = {
                        'symbol': symbol,
                        'side': 'BUY',
                        'qty': qty,
                        'price': price,
                        'confidence': confidence,
                        'entry_time': datetime.now(TIMEZONE).isoformat(),
                        'stop_loss': price * (1 - STOP_LOSS_PCT),
                        'take_profit': price * (1 + TAKE_PROFIT_PCT),
                        'order_id': order.id if hasattr(order, 'id') else None,
                        'status': 'OPEN'
                    }
                    
                    self.trade_log.append(trade_record)
                    
                    logger.info(
                        f"\n✓ TRADE EXECUTED:\n"
                        f"  Symbol: {symbol}\n"
                        f"  Qty: {qty}\n"
                        f"  Entry: ${price:.2f}\n"
                        f"  SL: ${trade_record['stop_loss']:.2f}\n"
                        f"  TP: ${trade_record['take_profit']:.2f}\n"
                        f"  Confidence: {confidence:.2%}"
                    )
        
        except Exception as e:
            logger.error(f"Trading check failed: {e}")
            import traceback
            traceback.print_exc()
    
    def rebalance_portfolio(self):
        """Close losing positions and rebalance"""
        try:
            positions = self.get_open_positions()
            
            if not positions:
                logger.info("No open positions to rebalance")
                return
            
            logger.info(f"Rebalancing {len(positions)} positions...")
            
            for symbol, position in positions.items():
                current_price = float(position.current_price)
                entry_price = float(position.avg_fill_price)
                qty = float(position.qty)
                
                # Check stop loss / take profit
                if entry_price > 0:
                    pnl_pct = (current_price - entry_price) / entry_price
                    
                    sl_hit = pnl_pct <= -STOP_LOSS_PCT
                    tp_hit = pnl_pct >= TAKE_PROFIT_PCT
                    
                    if sl_hit or tp_hit:
                        reason = "Stop Loss" if sl_hit else "Take Profit"
                        logger.info(f"Closing {symbol}: {reason} ({pnl_pct:+.2%})")
                        
                        # Close position
                        self.submit_order(symbol, qty, "sell")
                        
                        # Update trade log
                        for trade in reversed(self.trade_log):
                            if trade['symbol'] == symbol and trade['status'] == 'OPEN':
                                trade['status'] = 'CLOSED'
                                trade['exit_price'] = current_price
                                trade['exit_time'] = datetime.now(TIMEZONE).isoformat()
                                trade['pnl_pct'] = pnl_pct
                                trade['pnl_amount'] = qty * (current_price - entry_price)
                                break
            
            self.save_trade_history()
        
        except Exception as e:
            logger.error(f"Rebalancing failed: {e}")
    
    def scheduled_training(self):
        """Scheduled model retraining with new data"""
        try:
            self.trainer.train()
            
            # Reload predictor with new model
            self.predictor._load_model()
        
        except Exception as e:
            logger.error(f"Scheduled training failed: {e}")
    
    def get_performance_summary(self):
        """Get trading performance summary"""
        closed_trades = [t for t in self.trade_log if t.get('status') == 'CLOSED']
        
        if not closed_trades:
            return {
                'total_trades': len(self.trade_log),
                'closed_trades': 0,
                'win_rate': 0,
                'total_pnl': 0
            }
        
        wins = sum(1 for t in closed_trades if t.get('pnl_pct', 0) > 0)
        losses = len(closed_trades) - wins
        total_pnl = sum(t.get('pnl_amount', 0) for t in closed_trades)
        
        return {
            'total_trades': len(self.trade_log),
            'closed_trades': len(closed_trades),
            'wins': wins,
            'losses': losses,
            'win_rate': wins / len(closed_trades) if closed_trades else 0,
            'total_pnl': total_pnl,
            'avg_trade_pnl': total_pnl / len(closed_trades) if closed_trades else 0
        }
    
    def start(self):
        """Start the live trading system"""
        logger.info("\n" + "="*60)
        logger.info("STARTING LIVE TRADING SYSTEM")
        logger.info("="*60)
        
        # Check model
        if not self.predictor.is_model_ready():
            logger.error("No trained model found. Run ml_trainer.py first!")
            return False
        
        # Start scheduler
        self.scheduler.start()
        
        # Check market status
        self.scheduler.get_market_status()
        
        logger.info("✓ Live trading system started successfully")
        logger.info("  - Training scheduled for 8 PM daily")
        logger.info("  - Trading active during market hours")
        logger.info("  - Rebalancing scheduled for 4 AM daily")
        
        return True
    
    def stop(self):
        """Stop the live trading system"""
        logger.info("Stopping live trading system...")
        self.scheduler.stop()
        self.save_trade_history()
        logger.info("System stopped")


def main():
    """Main entry point"""
    trader = LiveTrader()
    
    try:
        if trader.start():
            logger.info("\nTrading system running. Press Ctrl+C to stop...")
            
            # Keep running
            while True:
                time.sleep(1)
    
    except KeyboardInterrupt:
        logger.info("\nShutting down...")
        trader.stop()
    
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        trader.stop()


if __name__ == "__main__":
    import time
    main()
