# .env Setup Guide

This project uses environment variables to store sensitive API keys securely.

## Setup Instructions

1. **Copy the example file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.services/.env` and add your credentials:**
   ```
   ALPACA_API_KEY=your_actual_key
   ALPACA_SECRET_KEY=your_actual_secret
   PAPER_MODE=True
   ```

3. **Install dependencies (if not already done):**
   ```bash
   pip install -r requirements.txt
   ```

## Security Notes

- ✅ `.env` is in `.gitignore` - it will never be committed to git
- ❌ Never commit API keys to version control
- ❌ Never share your `.env` file
- ✅ Use `.env.example` as a template for documentation

## Getting Your Alpaca API Keys

1. Go to https://app.alpaca.markets/
2. Sign up for a free paper trading account
3. Navigate to **Settings** → **API Keys**
4. Generate a new API key and secret
5. Copy them into your `.env` file

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `ALPACA_API_KEY` | Your Alpaca API key | `PK...` |
| `ALPACA_SECRET_KEY` | Your Alpaca secret key | `Gi5W...` |
| `PAPER_MODE` | Use paper trading (True/False) | `True` |

## Troubleshooting

If you get "ALPACA_API_KEY and ALPACA_SECRET_KEY must be set":
1. Ensure `.env` file exists in the `services/` directory
2. Check that you've added the variables with correct names
3. Make sure there are no extra spaces or quotes around values
4. Restart your Python environment/IDE
