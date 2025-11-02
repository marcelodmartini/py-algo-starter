import os
import time
import pandas as pd
import requests
import yfinance as yf
from datetime import datetime

# ------------------------------------------------------------
# AUTO FETCH — detecta fuente (yahoo o crypto) y guarda CSV
# ------------------------------------------------------------


def auto_fetch_to_csv(cfg: dict) -> str:
    """
    Descarga datos OHLCV automáticamente desde Yahoo Finance o Binance
    según el campo cfg["data"]["source"].
    Guarda un CSV local y devuelve el path.
    """
    csv_path = cfg["data"]["csv_path"]
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)

    source = cfg["data"].get("source", "yahoo").lower()
    symbol = cfg["data"]["symbol"]
    start = cfg["data"].get("start")
    end = cfg["data"].get("end")
    timeframe = cfg["data"].get("timeframe", "1h")
    limit = cfg["data"].get("limit", 1000)

    print(
        f"[INFO] Fetching source={source} symbol={symbol} timeframe={timeframe}")

    if source == "yahoo":
        df = fetch_yahoo(symbol, start, end, timeframe)
    elif source == "crypto":
        exchange = cfg["data"].get("exchange", "binance")
        df = fetch_binance(symbol, timeframe, start, limit)
    else:
        raise ValueError(f"Unknown data source: {source}")

    df.to_csv(csv_path, index=False)
    print(f"[OK] Saved data to {csv_path} ({len(df)} rows)")
    return csv_path

# ------------------------------------------------------------
# YAHOO FINANCE — acciones, ETFs, índices
# ------------------------------------------------------------


def fetch_yahoo(symbol: str, start=None, end=None, interval="1h") -> pd.DataFrame:
    print(f"[YF] Downloading {symbol} from Yahoo Finance...")
    df = yf.download(symbol, start=start, end=end,
                     interval=interval, progress=False)
    if df.empty:
        raise ValueError(f"No data found for {symbol} on Yahoo Finance.")
    df = df.rename(
        columns={
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
        }
    )
    df.reset_index(inplace=True)
    df["datetime"] = pd.to_datetime(
        df["Datetime"] if "Datetime" in df else df["Date"])
    df = df[["datetime", "open", "high", "low", "close", "volume"]]
    print(f"[YF] Got {len(df)} rows from Yahoo Finance.")
    return df

# ------------------------------------------------------------
# BINANCE — criptomonedas
# ------------------------------------------------------------


def fetch_binance(symbol: str, timeframe="1h", start=None, limit=1000) -> pd.DataFrame:
    """
    Baja velas OHLCV desde la API pública de Binance.
    """
    print(f"[BINANCE] Downloading {symbol} from Binance ({timeframe})...")
    endpoint = "https://api.binance.com/api/v3/klines"
    interval = timeframe.lower()
    df_list = []

    # Convertir fecha inicial a timestamp (ms)
    start_ts = None
    if start:
        start_ts = int(pd.Timestamp(start).timestamp() * 1000)

    while True:
        params = {
            "symbol": symbol.replace("/", ""),
            "interval": interval,
            "limit": limit,
        }
        if start_ts:
            params["startTime"] = start_ts

        r = requests.get(endpoint, params=params, timeout=10)
        if r.status_code != 200:
            raise Exception(f"Binance API error {r.status_code}: {r.text}")
        data = r.json()
        if not data:
            break

        frame = pd.DataFrame(
            data,
            columns=[
                "open_time",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "close_time",
                "quote_asset_volume",
                "num_trades",
                "taker_base_vol",
                "taker_quote_vol",
                "ignore",
            ],
        )

        frame["datetime"] = pd.to_datetime(frame["open_time"], unit="ms")
        frame = frame[["datetime", "open", "high", "low", "close", "volume"]].astype(
            {"open": float, "high": float, "low": float,
                "close": float, "volume": float}
        )
        df_list.append(frame)

        if len(data) < limit:
            break

        # Avanzar timestamp
        start_ts = data[-1][6]
        time.sleep(0.5)

    df = pd.concat(df_list, ignore_index=True)
    print(f"[BINANCE] Got {len(df)} rows for {symbol}.")
    return df
