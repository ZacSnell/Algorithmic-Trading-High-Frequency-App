"""
Continuous Trainer Daemon
- Runs scheduled full retraining nightly (configurable time)
- Optionally triggers training when market close is detected
- Saves models to models directory using MLTrainer.save_model
"""
import time
import logging
from datetime import datetime
import pytz
import os
from pathlib import Path
import schedule

# Local imports
from ml_trainer import MLTrainer
from config import POSITION_SIZE_PCT, ML_MODEL_TYPE
from market_scheduler import MarketScheduler

logger = logging.getLogger("continuous_trainer")
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# Configurable training time in Eastern Time (24h)
TRAIN_TIME_ET = os.getenv('CONTINUOUS_TRAIN_TIME_ET', '20:00')
MODELS_DIR = Path(__file__).parent.parent / "models"


def retrain_all_strategies():
    logger.info("Starting scheduled retraining for all strategies")
    trainer = MLTrainer()
    strategies = ['macd_crossover', 'scalping']  # extend as you add more

    results = {}
    for strategy in strategies:
        try:
            success = trainer.train(strategy=strategy)
            results[strategy] = 'SUCCESS' if success else 'FAILED'
        except Exception as e:
            logger.exception(f"Training failed for {strategy}: {e}")
            results[strategy] = 'ERROR'

    logger.info("Retraining complete")
    logger.info(results)


def schedule_daily_training(train_time_et: str = TRAIN_TIME_ET):
    # Convert ET time to local time if needed but schedule runs based on local machine time
    schedule.clear('retrain')
    schedule.every().day.at(train_time_et).do(retrain_all_strategies).tag('retrain')
    logger.info(f"Scheduled daily training at {train_time_et} ET (machine local time assumed)")


def run_forever():
    # Start market scheduler to be aware of market hours
    ms = MarketScheduler()
    ms.start()

    schedule_daily_training()

    logger.info("Continuous trainer daemon started")
    try:
        while True:
            schedule.run_pending()
            time.sleep(5)
    except KeyboardInterrupt:
        logger.info("Shutting down continuous trainer")
        ms.stop()


if __name__ == '__main__':
    run_forever()
