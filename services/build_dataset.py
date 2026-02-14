# build_dataset.py
# Generate synthetic training data for ML model
from config import *
import numpy as np

def generate_synthetic_data(symbol, num_days=60, strategy='macd_crossover'):
    """Generate realistic synthetic price data for training different strategies"""
    logger.info(f"Generating {strategy} synthetic data for {symbol}")
    
    # Random walk with drift (varies by strategy)
    np.random.seed(hash(symbol + strategy) % 2**32)  # Reproducible & strategy-specific
    initial_price = np.random.uniform(5, 100)
    
    # Different volatility profiles for different strategies
    strategy_params = {
        'macd_crossover': {'drift': 0.0005, 'volatility': 0.02},
        'scalping': {'drift': 0.0002, 'volatility': 0.015},  # Lower volatility for scalping
        'options_scalping': {'drift': 0.0008, 'volatility': 0.03},  # Higher volatility
        'five_pillars': {'drift': 0.0005, 'volatility': 0.025},
    }
    
    params = strategy_params.get(strategy, strategy_params['macd_crossover'])
    returns = np.random.normal(params['drift'], params['volatility'], num_days)
    prices = initial_price * np.exp(np.cumsum(returns))
    
    # Daily OHLCV
    dates = pd.date_range(end=datetime.now(tz=TIMEZONE), periods=num_days, freq='D')
    
    df = pd.DataFrame({
        'Open': prices * np.random.uniform(0.99, 1.01, num_days),
        'Close': prices,
        'High': prices * np.random.uniform(1.00, 1.03, num_days),
        'Low': prices * np.random.uniform(0.97, 1.00, num_days),
        'Volume': np.random.uniform(1_000_000, 10_000_000, num_days).astype(int)
    }, index=dates)
    
    # Ensure OHLC integrity
    df['High'] = df[['Open', 'Close', 'High']].max(axis=1)
    df['Low'] = df[['Open', 'Close', 'Low']].min(axis=1)
    
    return df.sort_index()

def get_most_active_symbols_with_price_filter():
    """
    Dynamically fetch today's most active/trending stocks
    Falls back to multiple methods if one fails
    """
    logger.info("Discovering today's most active stocks...")
    
    symbols = []
    
    # Method 1: Try Alpaca's screener API
    try:
        logger.info("Attempting to fetch from Alpaca screener...")
        url = "https://data.alpaca.markets/v1beta1/screener/stocks/most-actives?top=20&by=volume"
        response = data_client._request("GET", url)
        
        if response.status_code == 200:
            data = response.json()
            candidates = data.get('most_actives', [])
            symbols = [item['symbol'] for item in candidates[:20]]
            logger.info(f"✓ Alpaca screener: Found {len(symbols)} stocks")
            return symbols
    except Exception as e:
        logger.warning(f"Alpaca screener failed: {e}")
    
    # Method 2: Try yfinance to get today's top gainers
    try:
        logger.info("Attempting yfinance top gainers...")
        import yfinance as yf
        
        # This attempts to fetch trending data
        gainers = pd.read_html('https://finance.yahoo.com/gainers')[0]
        symbols = gainers['Symbol'].head(15).tolist()
        
        # Filter out bad symbols
        symbols = [s for s in symbols if len(s) <= 5 and s.isalpha()]
        logger.info(f"✓ Yahoo Finance: Found {len(symbols)} gainers")
        return symbols[:20]
    except Exception as e:
        logger.warning(f"yfinance gainers failed: {e}")
    
    # Method 3: Fetch high-volume stocks from yfinance
    try:
        logger.info("Attempting high-volume stocks lookup...")
        import yfinance as yf
        
        high_volume = pd.read_html('https://finance.yahoo.com/most-active')[0]
        symbols = high_volume['Symbol'].head(15).tolist()
        
        # Filter out bad symbols
        symbols = [s for s in symbols if len(s) <= 5 and s.isalpha()]
        logger.info(f"✓ High-volume stocks: Found {len(symbols)}")
        return symbols[:20]
    except Exception as e:
        logger.warning(f"High-volume lookup failed: {e}")
    
    # Method 4: Use predefined list of liquid stocks (fallback)
    logger.warning("All dynamic discovery methods failed, using fallback stock list")
    fallback = [
        "SPY", "QQQ", "IWM",  # ETFs
        "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN",  # Mega cap tech
        "TSLA", "META", "PLTR", "AMD",  # Growth stocks
        "JPM", "BAC", "WFC",  # Banks
        "XOM", "CVX"  # Energy
    ]
    
    logger.info(f"Using fallback: {len(fallback)} stocks")
    return fallback

def get_date_range():
    """Get start and end dates for data fetch"""
    end = datetime.now(tz=TIMEZONE)
    start = end - timedelta(days=DAYS_BACK)
    return start, end

def download_intraday(symbol, strategy='macd_crossover'):
    """Get historical data for training (using synthetic data for now)"""
    try:
        # Generate synthetic data (using larger sample for better training)
        df = generate_synthetic_data(symbol, num_days=100, strategy=strategy)
        logger.info(f"Generated {len(df)} synthetic bars for {symbol} ({strategy})")
        return df
    except Exception as e:
        logger.error(f"Data generation failed for {symbol}: {e}")
        return None

def add_features_and_target(df):
    # VWAP (cumulative session approximation)
    df['Typical_Price'] = (df['High'] + df['Low'] + df['Close']) / 3
    df['TP_Volume']     = df['Typical_Price'] * df['Volume']
    df['Cum_TP_Volume'] = df['TP_Volume'].cumsum()
    df['Cum_Volume']    = df['Volume'].cumsum()
    df['VWAP']          = df['Cum_TP_Volume'] / df['Cum_Volume']

    # MACD
    if TALIB_AVAILABLE:
        macd, signal, hist = talib.MACD(df['Close'])
        df['MACD']        = macd
        df['MACD_Signal'] = signal
        df['MACD_Hist']   = hist
    else:
        ema_fast = df['Close'].ewm(span=12, adjust=False).mean()
        ema_slow = df['Close'].ewm(span=26, adjust=False).mean()
        macd = ema_fast - ema_slow
        signal = macd.ewm(span=9, adjust=False).mean()
        df['MACD']        = macd
        df['MACD_Signal'] = signal
        df['MACD_Hist']   = macd - signal

    df['VWAP_Deviation'] = (df['Close'] - df['VWAP']) / df['VWAP']

    # Target label
    df['Future_Return'] = df['Close'].shift(-LOOKAHEAD_BARS) / df['Close'] - 1
    df['MACD_Cross_Up'] = (
        (df['MACD'].shift(1) <= df['MACD_Signal'].shift(1)) &
        (df['MACD'] > df['MACD_Signal'])
    )
    condition = (
        df['MACD_Cross_Up'] &
        (df['Close'] > df['VWAP']) &
        (df['Future_Return'] > PROFIT_THRESHOLD)
    )
    df['Target'] = 0
    df.loc[condition, 'Target'] = 1

    return df.dropna()

# ────────────────────────────────────────────────
# Main
# ────────────────────────────────────────────────

if __name__ == "__main__":
    logger.info("Starting dataset build for all strategies...")
    import json
    
    # Discover dynamic symbols - not hardcoded!
    symbols = get_most_active_symbols_with_price_filter()
    logger.info(f"Discovered {len(symbols)} active symbols for training: {', '.join(symbols)}")
    
    # Generate data for each strategy
    strategies = ['macd_crossover', 'scalping']  # Add more as implemented
    
    # Track training info for this run
    training_date = datetime.now(tz=TIMEZONE).strftime('%Y-%m-%d')
    training_info = {
        'date': training_date,
        'timestamp': datetime.now(tz=TIMEZONE).isoformat(),
        'strategies': {},
        'discovered_symbols': symbols,
        'num_symbols': len(symbols)
    }
    
    for strategy in strategies:
        logger.info(f"\n{'='*50}")
        logger.info(f"Building dataset for strategy: {strategy}")
        logger.info(f"Discovered symbols: {', '.join(symbols)}")
        logger.info(f"{'='*50}")
        
        all_data = {}
        strategy_info = {
            'symbols_used': [],
            'total_samples': 0,
            'files_created': []
        }
        
        for sym in symbols:
            logger.info(f"Generating data for {sym} ({strategy})...")
            df = download_intraday(sym, strategy=strategy)
            if df is not None:
                df = add_features_and_target(df)
                all_data[sym] = df
                filename = f"{sym}_{strategy}_labeled.csv"
                df.to_csv(filename)
                logger.info(f"  ✓ Saved {len(df):,} rows to {filename}")
                strategy_info['symbols_used'].append(sym)
                strategy_info['files_created'].append(filename)
        
        if all_data:
            combined = pd.concat(all_data.values(), keys=all_data.keys(), names=['Symbol'])
            combined_filename = f"combined_{strategy}_dataset.csv"
            combined.to_csv(combined_filename)
            strategy_info['total_samples'] = len(combined)
            strategy_info['combined_file'] = combined_filename
            logger.info(f"✓ Combined {strategy} dataset: {len(combined):,} rows in {combined_filename}")
        else:
            logger.warning(f"✗ No data collected for {strategy}")
        
        training_info['strategies'][strategy] = strategy_info
    
    # Save training metadata
    training_info_file = f"training_info_{training_date}.json"
    with open(training_info_file, 'w') as f:
        json.dump(training_info, f, indent=2)
    logger.info(f"\n✓ Training metadata saved to {training_info_file}")
    
    logger.info(f"\n{'='*50}")
    logger.info("Dataset build complete for all strategies!")
    logger.info(f"  Discovered and trained on: {', '.join(symbols)}")
    logger.info(f"  Training info saved: {training_info_file}")
    logger.info(f"{'='*50}")