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
    """Return list of symbols for training (using synthetic data)"""
    # Since we're using synthetic data, we don't need to filter
    symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN", "META", "NVDA", "AMD", "PLTR", "XOM"]
    logger.info(f"Using {len(symbols)} symbols for synthetic data generation")
    return symbols

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
    symbols = get_most_active_symbols_with_price_filter()
    
    # Generate data for each strategy
    strategies = ['macd_crossover', 'scalping']  # Add more as implemented
    
    for strategy in strategies:
        logger.info(f"\n{'='*50}")
        logger.info(f"Building dataset for strategy: {strategy}")
        logger.info(f"{'='*50}")
        
        all_data = {}
        
        for sym in symbols:
            logger.info(f"Processing {sym} ({strategy})")
            df = download_intraday(sym, strategy=strategy)
            if df is not None:
                df = add_features_and_target(df)
                all_data[sym] = df
                filename = f"{sym}_{strategy}_labeled.csv"
                df.to_csv(filename)
                logger.info(f"Saved {len(df):,} rows to {filename}")
        
        if all_data:
            combined = pd.concat(all_data.values(), keys=all_data.keys(), names=['Symbol'])
            combined_filename = f"combined_{strategy}_dataset.csv"
            combined.to_csv(combined_filename)
            logger.info(f"Combined {strategy} dataset saved: {len(combined):,} rows to {combined_filename}")
        else:
            logger.warning(f"No data collected for {strategy}")
    
    logger.info(f"\n{'='*50}")
    logger.info("Dataset build complete for all strategies!")
    logger.info(f"{'='*50}")