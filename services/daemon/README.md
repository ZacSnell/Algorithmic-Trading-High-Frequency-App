Continuous Trainer Daemon

This daemon runs scheduled model retraining and can be hosted 24/7 using Docker or a process manager.

Usage (locally):

1. Ensure you have a Python venv with project dependencies installed.
2. From project root run:
   python -u services/daemon/continuous_trainer.py

Docker (recommended for 24/7):

1. Set up `.env` at project root with credentials and any env vars.
2. Start services with:
   docker-compose up -d --build

Notes:
- The trainer uses `MLTrainer.train(strategy)` for each implemented strategy.
- Extend `strategies` list in `continuous_trainer.py` to include new strategies.
- In production replace schedule with a real scheduler and use orchestration (Kubernetes) for scaling and self-healing.
