Headless Live Trader Service

This runs the `LiveTrader` headless (no GUI) for 24/7 operation. It expects `.env` to contain Alpaca credentials and other config.

Build and run with Docker Compose (project root):

```bash
docker compose up -d --build live_trader
```

Notes:
- Logs are available via `docker compose logs -f live_trader`.
- Ensure `services/models` and any needed directories are mounted if you want persistence.
