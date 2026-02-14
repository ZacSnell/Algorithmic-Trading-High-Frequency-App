# build_dataset.py
from config import *  # ← This brings in everything!
API_KEY = "YOUR_ALPACA_PAPER_KEY"
API_SECRET = "YOUR_ALPACA_PAPER_SECRET"
PAPER = True

# Clients
trade_client = TradingClient(API_KEY, API_SECRET, paper=PAPER)
data_client = StockHistoricalDataClient(API_KEY, API_SECRET)

NUM_SYMBOLS = 20          # Top 20 most active by volume
DAYS_BACK = 30            # Recent history for each symbol
INTERVAL = "1m"           # 1-minute bars

def get_most_active_symbols(top_n=NUM_SYMBOLS):
    """
    Fetch top most active stocks from Alpaca screener (real-time volume).
    Returns list of symbols (e.g., ['NVDA', 'TSLA', ...])
    """
    # Alpaca most-actives endpoint (via raw request or client if supported)
    # Note: alpaca-py may need update; fallback to manual if needed
    from alpaca.common.requests import GetRequest
    
    url = f"https://data.alpaca.markets/v1beta1/screener/stocks/most-actives?top={top_n}&by=volume"
    response = data_client._request("GET", url)  # Internal helper; adjust if version changes
    
    if response.status_code != 200:
        print("Error fetching most active:", response.text)
        return ["AAPL", "TSLA", "NVDA", "AMD", "SPY"]  # Hardcoded fallback
    
    data = response.json()
    symbols = [item['symbol'] for item in data.get('most_actives', [])]
    print(f"Fetched {len(symbols)} most active symbols: {symbols[:5]}...")
    return symbols

def download_intraday(symbol):
    # Use yfinance for simplicity (Alpaca bars work too, but yf easier for bulk)
    end = datetime.now(pytz.timezone('US/Eastern'))
    start = end - timedelta(days=DAYS_BACK * 1.5)
    
    df = yf.download(symbol, start=start, end=end, interval=INTERVAL, progress=False)
    
    if df.empty:
        print(f"No 1-min data for {symbol}")
        return None
    
    df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
    df.index = df.index.tz_convert('US/Eastern')
    df = df.sort_index()
    df = df[df['Volume'] > 0]
    return df

def add_features_and_target(df, lookahead_bars=5, profit_threshold=0.001):
    # VWAP approx
    df['Typical_Price'] = (df['High'] + df['Low'] + df['Close']) / 3
    df['TP_Volume'] = df['Typical_Price'] * df['Volume']
    df['Cum_TP_Volume'] = df['TP_Volume'].cumsum()
    df['Cum_Volume'] = df['Volume'].cumsum()
    df['VWAP'] = df['Cum_TP_Volume'] / df['Cum_Volume']
    
    # MACD (TA-Lib or pandas fallback)
    try:
        macd, signal, hist = talib.MACD(df['Close'])
        df['MACD'] = macd
        df['MACD_Signal'] = signal
        df['MACD_Hist'] = hist
    except:
        ema_fast = df['Close'].ewm(span=12, adjust=False).mean()
        ema_slow = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = ema_fast - ema_slow
        df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
    
    df['VWAP_Deviation'] = (df['Close'] - df['VWAP']) / df['VWAP']
    
    # Target: 1 if potential profitable buy setup
    df['Future_Return'] = df['Close'].shift(-lookahead_bars) / df['Close'] - 1
    df['MACD_Cross_Up'] = (df['MACD'].shift(1) <= df['MACD_Signal'].shift(1)) & (df['MACD'] > df['MACD_Signal'])
    condition = df['MACD_Cross_Up'] & (df['Close'] > df['VWAP']) & (df['Future_Return'] > profit_threshold)
    df['Target'] = 0
    df.loc[condition, 'Target'] = 1
    
    return df.dropna()

# Main execution
symbols = get_most_active_symbols(NUM_SYMBOLS)

all_data = {}
for sym in symbols:
    print(f"Processing {sym}...")
    df = download_intraday(sym)
    if df is not None:
        df = add_features_and_target(df)
        all_data[sym] = df
        df.to_csv(f"{sym}_1min_labeled.csv")
        print(f"Saved {len(df)} rows for {sym}")

# Combine for ML training (optional)
if all_data:
    combined = pd.concat(all_data.values(), keys=all_data.keys(), names=['Symbol'])
    combined.to_csv("combined_dataset.csv")
    print(f"Total rows in combined dataset: {len(combined)}")