
import os
import pandas as pd
from typing import Optional

def _ensure_cols(df: pd.DataFrame, mapping: dict):
    """Rename columns and enforce OHLCV order."""
    df = df.rename(columns=mapping)
    cols = ["datetime","open","high","low","close","volume"]
    for c in cols:
        if c not in df.columns:
            raise ValueError(f"Missing column '{c}' in fetched dataframe")
    return df[cols]

def fetch_crypto_ccxt(symbol: str, timeframe: str = "1h", limit: int = 5000, exchange: str = "binance",
                      since: Optional[str] = None) -> pd.DataFrame:
    """
    Fetch OHLCV for crypto using ccxt.
    Example:
        df = fetch_crypto_ccxt("BTC/USDT", "1h", 5000, "binance")
    """
    import ccxt
    ex = getattr(ccxt, exchange)()
    params = {}
    ms_since = None
    if since:
        ms_since = int(pd.Timestamp(since).timestamp() * 1000)
    bars = ex.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit, since=ms_since, params=params)
    df = pd.DataFrame(bars, columns=["datetime","open","high","low","close","volume"])
    df["datetime"] = pd.to_datetime(df["datetime"], unit="ms")
    return _ensure_cols(df, {})

def fetch_yahoo(symbol: str, interval: str = "1h", start: Optional[str] = None, end: Optional[str] = None) -> pd.DataFrame:
    """
    Fetch OHLCV for equities/ETFs using yfinance.
    Example:
        df = fetch_yahoo("SPY", "1h", "2020-01-01", None)
    """
    import yfinance as yf
    df = yf.download(symbol, start=start, end=end, interval=interval, progress=False)
    if df.empty:
        raise ValueError(f"No data returned for {symbol} {interval}")
    df = df.reset_index()
    mapping = {}
    if "Date" in df.columns:
        mapping["Date"] = "datetime"
    if "Datetime" in df.columns:
        mapping["Datetime"] = "datetime"
    mapping.update({"Open":"open","High":"high","Low":"low","Close":"close","Volume":"volume"})
    return _ensure_cols(df, mapping)

def save_csv(df: pd.DataFrame, out_path: str):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    df.to_csv(out_path, index=False)
    return out_path

def auto_fetch_to_csv(cfg: dict) -> str:
    """
    Uses config fields to auto-fetch and persist CSV, returning the final CSV path.
    Expected config structure:

    data:
      auto_fetch: true
      source: "crypto" | "yahoo"
      symbol: "BTC/USDT" | "SPY"
      exchange: "binance"        # only for crypto
      timeframe: "1H"            # (crypto) mapped to ccxt: 1H->1h
      interval: "1h"             # (yahoo) e.g., 1m/5m/15m/1h/1d
      start: "2020-01-01"
      end: null
      csv_path: "data/ASSET.csv"
      limit: 5000                # crypto max bars

    Returns:
      csv_path (str)
    """
    d = cfg.get("data", {})
    csv_path = d.get("csv_path", "data/ASSET.csv")
    source = d.get("source", None)
    if not d.get("auto_fetch", False) or not source:
        return csv_path

    if source == "crypto":
        symbol = d.get("symbol", "BTC/USDT")
        exchange = d.get("exchange", "binance")
        tf_map = {"1min":"1m","5min":"5m","15min":"15m","1H":"1h","4H":"4h","1D":"1d"}
        timeframe = tf_map.get(d.get("timeframe","1H"), "1h")
        limit = int(d.get("limit", 5000))
        since = d.get("start", None)
        df = fetch_crypto_ccxt(symbol=symbol, timeframe=timeframe, limit=limit, exchange=exchange, since=since)
    elif source == "yahoo":
        symbol = d.get("symbol", "SPY")
        interval = d.get("interval", "1h")
        start = d.get("start", None)
        end = d.get("end", None)
        df = fetch_yahoo(symbol=symbol, interval=interval, start=start, end=end)
    else:
        raise ValueError(f"Unknown data.source '{source}'")

    save_csv(df, csv_path)
    return csv_path
