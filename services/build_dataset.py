# build_dataset.py
from config import *

def get_most_active_symbols_with_price_filter():
    """
    Fetch more candidates than needed, then filter by price range.
    """
    logger.info(f"Fetching top {FETCH_TOP_BEFORE_FILTER} most active stocks...")

    url = f"https://data.alpaca.markets/v1beta1/screener/stocks/most-actives?top={FETCH_TOP_BEFORE_FILTER}&by=volume"

    try:
        # Note: alpaca-py does not have a clean public method for this screener yet,
        # so we use the low-level request (this may change in future versions)
        response = data_client._request("GET", url)
        if response.status_code != 200:
            raise Exception(f"API error {response.status_code}: {response.text}")

        data = response.json()
        candidates = data.get('most_actives', [])
        if not candidates:
            raise Exception("No most-actives returned")

        symbols = [item['symbol'] for item in candidates]
        logger.info(f"Got {len(symbols)} candidates")
    except Exception as e:
        logger.error(f"Failed to fetch most-actives: {e}")
        symbols = ["AMC", "NIO", "SOFI", "F", "RIVN", "PLTR", "LCID"]  # cheap active fallback

    # Filter by price
    filtered = []
    for sym in symbols:
        try:
            # Get latest bar (most recent close)
            params = StockBarsRequest(
                symbol_or_symbols=sym,
                timeframe=TimeFrame.Minute,
                limit=1
            )
            bars = data_client.get_stock_bars(params)
            if bars and sym in bars and len(bars[sym]) > 0:
                price = bars[sym][-1].close
                if MIN_PRICE_FILTER <= price <= MAX_PRICE_FILTER:
                    filtered.append(sym)
                    logger.info(f"Included {sym} @ ${price:.2f}")
                # else: logger.debug(f"Excluded {sym} @ ${price:.2f}")
            else:
                logger.debug(f"No recent bar for {sym}")
        except Exception as e:
            logger.warning(f"Price fetch failed for {sym}: {e}")

    if not filtered:
        logger.warning("No symbols passed price filter → using fallback list")
        filtered = ["AMC", "NIO", "SOFI", "F", "RIVN"]

    final_list = filtered[:NUM_TOP_SYMBOLS]
    logger.info(f"Final list ({len(final_list)} symbols): {final_list}")
    return final_list

def download_intraday(symbol):
    start, end = get_date_range()
    try:
        df = yf.download(symbol, start=start, end=end, interval=INTERVAL, progress=False)
        if df.empty:
            logger.warning(f"No data from yfinance for {symbol}")
            return None

        df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
        df.index = df.index.tz_convert(TIMEZONE)
        df = df.sort_index()
        df = df[df['Volume'] > 0]
        return df
    except Exception as e:
        logger.error(f"yfinance download failed for {symbol}: {e}")
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
    logger.info("Starting dataset build...")
    symbols = get_most_active_symbols_with_price_filter()

    all_data = {}
    for sym in symbols:
        logger.info(f"Processing {sym}")
        df = download_intraday(sym)
        if df is not None:
            df = add_features_and_target(df)
            all_data[sym] = df
            filename = f"{sym}_1min_labeled.csv"
            df.to_csv(filename)
            logger.info(f"Saved {len(df):,} rows to {filename}")

    if all_data:
        combined = pd.concat(all_data.values(), keys=all_data.keys(), names=['Symbol'])
        combined.to_csv("combined_dataset.csv")
        logger.info(f"Combined dataset saved: {len(combined):,} rows")
    else:
        logger.warning("No data collected")