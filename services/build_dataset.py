# build_dataset.py - FIXED DST ERROR
from config import *
import numpy as np
import json
from datetime import datetime

def generate_synthetic_data(symbol, num_days=2000, strategy='macd_crossover'):
    logger.info(f"Generating {strategy} synthetic data for {symbol} ({num_days} bars)")
    np.random.seed(hash(symbol + strategy) % 2**32)
    initial_price = np.random.uniform(5, 100)
    params = {'drift': 0.0005, 'volatility': 0.018}
    returns = np.random.normal(params['drift'], params['volatility'], num_days)
    prices = initial_price * np.exp(np.cumsum(returns))

    # FIXED: Generate dates without timezone first, then localize with ambiguous='infer'
    dates = pd.date_range(end=datetime.now(), periods=num_days, freq='D')
    dates = dates.tz_localize(TIMEZONE, ambiguous='infer', nonexistent='shift_forward')

    df = pd.DataFrame({
        'Open': prices * np.random.uniform(0.99, 1.01, num_days),
        'Close': prices,
        'High': prices * np.random.uniform(1.00, 1.03, num_days),
        'Low': prices * np.random.uniform(0.97, 1.00, num_days),
        'Volume': np.random.uniform(1_000_000, 10_000_000, num_days).astype(int)
    }, index=dates)

    df['High'] = df[['Open', 'Close', 'High']].max(axis=1)
    df['Low'] = df[['Open', 'Close', 'Low']].min(axis=1)
    return df.sort_index()

def get_most_active_symbols_with_price_filter():
    logger.info("Discovering today's most active stocks...")
    fallback = ["SPY", "QQQ", "IWM", "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "TSLA", "META", "PLTR", "AMD", "JPM", "BAC", "WFC", "XOM", "CVX"]
    logger.info(f"Using fallback: {len(fallback)} stocks")
    return fallback

def download_intraday(symbol, strategy='macd_crossover'):
    try:
        df = generate_synthetic_data(symbol, num_days=2000, strategy=strategy)
        logger.info(f"Generated {len(df)} synthetic bars for {symbol}")
        return df
    except Exception as e:
        logger.error(f"Data generation failed for {symbol}: {e}")
        return None

def add_features_and_target(df):
    df['Typical_Price'] = (df['High'] + df['Low'] + df['Close']) / 3
    df['TP_Volume'] = df['Typical_Price'] * df['Volume']
    df['Cum_TP_Volume'] = df['TP_Volume'].cumsum()
    df['Cum_Volume'] = df['Volume'].cumsum()
    df['VWAP'] = df['Cum_TP_Volume'] / df['Cum_Volume']
    df['VWAP_Deviation'] = (df['Close'] - df['VWAP']) / df['VWAP']

    if TALIB_AVAILABLE:
        macd, signal, hist = talib.MACD(df['Close'])
        df['MACD'] = macd
        df['MACD_Signal'] = signal
        df['MACD_Hist'] = hist
        df['RSI'] = talib.RSI(df['Close'], timeperiod=14)
        df['ATR'] = talib.ATR(df['High'], df['Low'], df['Close'], timeperiod=14)
        df['OBV'] = talib.OBV(df['Close'], df['Volume'])
        upper, middle, lower = talib.BBANDS(df['Close'], timeperiod=20)
        df['Bollinger_Width'] = (upper - lower) / middle
    else:
        ema_fast = df['Close'].ewm(span=12, adjust=False).mean()
        ema_slow = df['Close'].ewm(span=26, adjust=False).mean()
        macd = ema_fast - ema_slow
        signal = macd.ewm(span=9, adjust=False).mean()
        df['MACD'] = macd
        df['MACD_Signal'] = signal
        df['MACD_Hist'] = macd - signal
        df['RSI'] = 50.0
        df['ATR'] = df['High'] - df['Low']
        df['OBV'] = df['Volume'].cumsum()
        df['Bollinger_Width'] = 0.05

    df['High_Low_Range'] = df['High'] - df['Low']
    df['Close_vs_High'] = df['Close'] / df['High']
    df['ZScore'] = (df['Close'] - df['Close'].rolling(20).mean()) / df['Close'].rolling(20).std()
    df['Volume_SMA_Ratio'] = df['Volume'] / df['Volume'].rolling(20).mean()
    df['Volatility_Ratio'] = df['Close'].rolling(20).std() / df['Close'].rolling(100).std()

    df['Future_Return'] = df['Close'].shift(-LOOKAHEAD_BARS) / df['Close'] - 1
    df['MACD_Cross_Up'] = (df['MACD'].shift(1) <= df['MACD_Signal'].shift(1)) & (df['MACD'] > df['MACD_Signal'])
    condition = (df['MACD_Cross_Up'] & (df['Close'] > df['VWAP']) & (df['Future_Return'] > PROFIT_THRESHOLD * 0.5))
    df['Target'] = 0
    df.loc[condition, 'Target'] = 1

    df = df.iloc[:-LOOKAHEAD_BARS]
    df = df.fillna(0)
    return df

if __name__ == "__main__":
    logger.info("Starting dataset build...")
    symbols = get_most_active_symbols_with_price_filter()
    strategies = ['macd_crossover', 'scalping']
    for strategy in strategies:
        all_data = {}
        for sym in symbols:
            df = download_intraday(sym, strategy)
            if df is not None:
                df = add_features_and_target(df)
                all_data[sym] = df
                df.to_csv(f"{sym}_{strategy}_labeled.csv")
                logger.info(f"Saved {len(df):,} rows to {sym}_{strategy}_labeled.csv")
        if all_data:
            combined = pd.concat(all_data.values(), keys=all_data.keys())
            combined.to_csv(f"combined_{strategy}_dataset.csv")
            logger.info(f"Combined {strategy} dataset: {len(combined):,} rows")
    logger.info("Dataset build complete!")