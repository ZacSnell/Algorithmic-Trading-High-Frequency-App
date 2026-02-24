# market_scheduler.py - FIXED VERSION
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from config import *
import schedule
import threading
import time
from datetime import datetime

def now_eastern():
    """Helper to get current time in US/Eastern timezone"""
    return datetime.now(TIMEZONE)

class MarketScheduler:
    def __init__(self, training_callback=None, trading_callback=None, rebalance_callback=None):
        self.training_callback = training_callback
        self.trading_callback = trading_callback
        self.rebalance_callback = rebalance_callback
        self.scheduler_thread = None
        self.should_run = False

    def is_market_open(self):
        """Check if US stock market is currently open"""
        now = now_eastern()

        if now.weekday() >= 5:  # Saturday or Sunday
            return False

        market_open = now.replace(hour=MARKET_OPEN_HOUR, minute=MARKET_OPEN_MIN, second=0, microsecond=0)
        market_close = now.replace(hour=MARKET_CLOSE_HOUR, minute=MARKET_CLOSE_MIN, second=0, microsecond=0)

        return market_open <= now < market_close

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
            "status": status,
            "time": now
        }

    def schedule_jobs(self):
        """Set up scheduled tasks"""
        schedule.every().day.at(TRAIN_TIME).do(self._run_training)
        schedule.every().day.at(REBALANCE_TIME).do(self._run_rebalance)
        schedule.every().minute.do(self._run_trading_if_market_open)

        logger.info(f"Scheduled training at {TRAIN_TIME} ET daily")
        logger.info(f"Scheduled rebalance at {REBALANCE_TIME} ET daily")
        logger.info("Scheduled trading to check every minute (market hours only)")

    def _run_training(self):
        if self.training_callback:
            logger.info("\n" + "="*60)
            logger.info("SCHEDULED TRAINING STARTED")
            logger.info("="*60)
            try:
                self.training_callback()
            except Exception as e:
                logger.error(f"Training failed: {e}")

    def _run_trading_if_market_open(self):
        if self.is_market_open() and self.trading_callback:
            try:
                self.trading_callback()
            except Exception as e:
                logger.error(f"Trading callback failed: {e}")

    def _run_rebalance(self):
        if self.rebalance_callback:
            logger.info("\n" + "="*60)
            logger.info("SCHEDULED REBALANCE STARTED")
            logger.info("="*60)
            try:
                self.rebalance_callback()
            except Exception as e:
                logger.error(f"Rebalancing failed: {e}")

    def _scheduler_loop(self):
        logger.info("Scheduler thread started")
        while self.should_run:
            try:
                schedule.run_pending()
                time.sleep(5)
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(5)
        logger.info("Scheduler thread stopped")

    def start(self):
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            logger.warning("Scheduler already running")
            return False

        self.schedule_jobs()
        self.should_run = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()

        logger.info("Market scheduler started")
        return True

    def stop(self):
        self.should_run = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        logger.info("Market scheduler stopped")

if __name__ == "__main__":
    scheduler = MarketScheduler()
    scheduler.start()
    input("Press Enter to stop...")
    scheduler.stop()