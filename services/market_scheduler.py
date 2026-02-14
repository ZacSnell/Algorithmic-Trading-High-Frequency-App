# market_scheduler.py
# Handles market hours detection and scheduled training/trading activities

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from config import *
import schedule
import threading
import time


class MarketScheduler:
    """
    Manages the trading schedule based on US market hours.
    - Trains models during market closed hours (8 PM)
    - Rebalances portfolio before market open (4 AM)
    - Runs live trading during market hours
    """
    
    def __init__(self, training_callback=None, trading_callback=None, rebalance_callback=None):
        """
        Args:
            training_callback: Function to call for model training
            trading_callback: Function to call for live trading
            rebalance_callback: Function to call for portfolio rebalancing
        """
        self.training_callback = training_callback
        self.trading_callback = trading_callback
        self.rebalance_callback = rebalance_callback
        self.scheduler_thread = None
        self.should_run = False
    
    def is_market_open(self):
        """Check if US stock market is currently open"""
        now = now_eastern()
        
        # Market is closed on weekends
        if now.weekday() >= 5:  # Saturday=5, Sunday=6
            return False
        
        # Market hours: 9:30 AM - 4:00 PM ET
        market_open = now.replace(hour=MARKET_OPEN_HOUR, minute=MARKET_OPEN_MIN, second=0, microsecond=0)
        market_close = now.replace(hour=MARKET_CLOSE_HOUR, minute=MARKET_CLOSE_MIN, second=0, microsecond=0)
        
        is_open = market_open <= now < market_close
        return is_open
    
    def get_market_status(self):
        """Get detailed market status"""
        now = now_eastern()
        day_name = now.strftime("%A")
        
        if now.weekday() >= 5:
            status = "CLOSED (Weekend)"
        elif self.is_market_open():
            market_close = now.replace(hour=MARKET_CLOSE_HOUR, minute=MARKET_CLOSE_MIN)
            minutes_until_close = int((market_close - now).total_seconds() / 60)
            status = f"OPEN (closes in {minutes_until_close}m)"
        else:
            status = "CLOSED (After Hours)"
        
        logger.info(f"Market Status: {status} | {day_name} {now.strftime('%H:%M:%S')}")
        return {
            "is_open": self.is_market_open(),
            "time": now,
            "status": status,
            "day": day_name
        }
    
    def schedule_jobs(self):
        """Set up scheduled tasks"""
        
        # Train model daily at 8 PM ET (after market close)
        schedule.every().day.at(TRAIN_TIME).do(self._run_training)
        logger.info(f"Scheduled training at {TRAIN_TIME} ET daily")
        
        # Rebalance portfolio at 4 AM ET (before market open)
        schedule.every().day.at(REBALANCE_TIME).do(self._run_rebalance)
        logger.info(f"Scheduled rebalance at {REBALANCE_TIME} ET daily")
        
        # Run trading checks every minute during market hours
        schedule.every().minute.do(self._run_trading_if_market_open)
        logger.info("Scheduled trading to check every minute (market hours only)")
    
    def _run_training(self):
        """Wrapper for training callback"""
        if self.training_callback:
            logger.info("\n" + "="*60)
            logger.info("SCHEDULED TRAINING STARTED")
            logger.info("="*60)
            try:
                self.training_callback()
                logger.info("Training completed successfully")
            except Exception as e:
                logger.error(f"Training failed: {e}")
                import traceback
                traceback.print_exc()
    
    def _run_trading_if_market_open(self):
        """Only run trading if market is open"""
        if self.is_market_open():
            if self.trading_callback:
                try:
                    self.trading_callback()
                except Exception as e:
                    logger.error(f"Trading callback failed: {e}")
                    import traceback
                    traceback.print_exc()
    
    def _run_rebalance(self):
        """Wrapper for rebalance callback"""
        if self.rebalance_callback:
            logger.info("\n" + "="*60)
            logger.info("SCHEDULED REBALANCE STARTED")
            logger.info("="*60)
            try:
                self.rebalance_callback()
                logger.info("Rebalancing completed successfully")
            except Exception as e:
                logger.error(f"Rebalancing failed: {e}")
                import traceback
                traceback.print_exc()
    
    def _scheduler_loop(self):
        """Run the scheduler in a loop"""
        logger.info("Scheduler thread started")
        
        while self.should_run:
            try:
                schedule.run_pending()
                time.sleep(5)  # Check schedule every 5 seconds
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(5)
        
        logger.info("Scheduler thread stopped")
    
    def start(self):
        """Start the scheduler in a background thread"""
        if self.scheduler_thread is not None and self.scheduler_thread.is_alive():
            logger.warning("Scheduler already running")
            return False
        
        self.schedule_jobs()
        self.should_run = True
        
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=False)
        self.scheduler_thread.start()
        
        logger.info("Market scheduler started")
        return True
    
    def stop(self):
        """Stop the scheduler"""
        self.should_run = False
        
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=10)
        
        logger.info("Market scheduler stopped")
    
    def run_training_now(self):
        """Manually trigger training (for testing)"""
        logger.info("Manually triggering training...")
        self._run_training()
    
    def run_trading_now(self):
        """Manually trigger trading (for testing)"""
        if self.trading_callback:
            logger.info("Manually triggering trading...")
            self._run_trading_if_market_open()
    
    def run_rebalance_now(self):
        """Manually trigger rebalancing (for testing)"""
        logger.info("Manually triggering rebalance...")
        self._run_rebalance()


if __name__ == "__main__":
    # Test scheduler without callbacks
    scheduler = MarketScheduler()
    
    logger.info("Testing MarketScheduler...")
    status = scheduler.get_market_status()
    
    logger.info(f"\nMarket is {'OPEN' if status['is_open'] else 'CLOSED'}")
    logger.info(f"Next training scheduled at: {TRAIN_TIME} ET")
    logger.info(f"Next rebalance scheduled at: {REBALANCE_TIME} ET")
