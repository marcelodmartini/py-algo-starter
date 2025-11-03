import os
import time
import pandas as pd
import requests
import yfinance as yf
from typing import Optional, List

CRYPTO_QUOTES_PRIORITY: List[str] = ["USDT", "USD", "BUSD"]


def _normalize_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    cols = ["datetime", "open", "high", "low", "close", "volume"]
    if not set(cols).issubset(df.columns):
        return pd.DataFrame(columns=cols)
    out = df[cols].dropna().copy().sort_values("datetime")
    for c in ["open", "high", "low", "close", "volume"]:
        out[c] = out[c].astype(float)
    return out


def _is_probably_crypto(symbol: str) -> bool:
    s = symbol.strip().upper()
    if "/" in s:
        return True
    return s.isalpha() and (3 <= len(s) <= 5)


def _yahoo_candidates(symbol: str) -> List[str]:
    s = symbol.strip().upper()
    if "/" in s:
        base = s.split("/")[0]
        return [f"{base}-USD"]
    if "-" in s:
        return [s]
    if _is_probably_crypto(s):
        return [f"{s}-USD", s]
    return [s]


def _binance_candidates(symbol: str) -> List[str]:
    s = symbol.strip().upper()
    if "/" in s:
        return [s]
    if _is_probably_crypto(s):
        return [f"{s}/{q}" for q in CRYPTO_QUOTES_PRIORITY]
    return []


def fetch_yahoo(symbol: str, start: Optional[str] = None, end: Optional[str] = None,
                interval: str = "1h") -> pd.DataFrame:
    kwargs = {}
    if start:
        kwargs["start"] = pd.to_datetime(start)
    if end:
        kwargs["end"] = pd.to_datetime(end)

    print(f"[YF] Downloading {symbol} (interval={interval})...")
    df = yf.download(symbol, interval=interval, progress=False, **kwargs)
    if df is None or df.empty:
        print(f"[YF] Empty for {symbol}")
        return pd.DataFrame(columns=["datetime", "open", "high", "low", "close", "volume"])

    rename = {}
    if "Date" in df.columns:
        rename["Date"] = "datetime"
    if "Datetime" in df.columns:
        rename["Datetime"] = "datetime"
    for k in ("Open", "High", "Low", "Close", "Volume"):
        if k in df.columns:
            rename[k] = k.lower()
    df = df.rename(columns=rename).reset_index()

    if "datetime" not in df.columns:
        return pd.DataFrame(columns=["datetime", "open", "high", "low", "close", "volume"])

    out = df[["datetime", "open", "high", "low", "close", "volume"]]
    print(f"[YF] Got {len(out)} rows for {symbol}")
    return _normalize_ohlcv(out)


def fetch_binance(symbol: str, timeframe: str = "1h", start: Optional[str] = None,
                  limit: int = 1000) -> pd.DataFrame:
    endpoint = "https://api.binance.com/api/v3/klines"
    interval = timeframe.lower()
    df_list = []
    start_ts = int(pd.Timestamp(start, tz="UTC").timestamp()
                   * 1000) if start else None
    symbol_noslash = symbol.replace("/", "").upper()

    while True:
        params = {"symbol": symbol_noslash,
                  "interval": interval, "limit": int(limit)}
        if start_ts:
            params["startTime"] = start_ts
        r = requests.get(endpoint, params=params, timeout=15)
        if r.status_code != 200:
            print(
                f"[BINANCE] API error {r.status_code} for {symbol_noslash}: {r.text}")
            return pd.DataFrame(columns=["datetime", "open", "high", "low", "close", "volume"])
        data = r.json()
        if not data:
            break

        frame = pd.DataFrame(data, columns=[
            "open_time", "open", "high", "low", "close", "volume",
            "close_time", "quote_asset_volume", "num_trades",
            "taker_base_vol", "taker_quote_vol", "ignore",
        ])
        frame["datetime"] = pd.to_datetime(
            frame["open_time"], unit="ms", utc=True)
        frame = frame[["datetime", "open", "high",
                       "low", "close", "volume"]].astype(float)
        df_list.append(frame)

        if len(data) < limit:
            break
        start_ts = data[-1][6]
        time.sleep(0.25)

    if not df_list:
        return pd.DataFrame(columns=["datetime", "open", "high", "low", "close", "volume"])
    df = pd.concat(df_list, ignore_index=True)
    print(f"[BINANCE] Got {len(df)} rows for {symbol_noslash}")
    return _normalize_ohlcv(df)


def auto_fetch_to_csv(cfg: dict) -> str:
    """
    1) Prueba Yahoo con candidatos (equity/ETF/cripto tipo BTC-USD).
    2) Si vacío y parece cripto → prueba Binance (/USDT → /USD → /BUSD).
    3) Guarda CSV y retorna el path. Si todo falla, crea dummy para no romper.
    """
    csv_path = cfg["data"]["csv_path"]
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)

    symbol = str(cfg["data"].get("symbol", "SPY")).strip()
    interval = str(cfg["data"].get("interval", "1h")).lower()    # Yahoo
    timeframe = str(cfg["data"].get("timeframe", "1h")).lower()   # Binance
    start = cfg["data"].get("start")
    end = cfg["data"].get("end")
    limit = int(cfg["data"].get("limit", 5000))

    print(
        f"[AUTO] symbol={symbol} interval(YF)={interval} timeframe(BIN)={timeframe}")

    for yc in _yahoo_candidates(symbol):
        try:
            df_y = fetch_yahoo(yc, start=start, end=end, interval=interval)
            if not df_y.empty:
                df_y.to_csv(csv_path, index=False)
                print(
                    f"[AUTO] Yahoo OK → {yc} (rows={len(df_y)}) → {csv_path}")
                return csv_path
        except Exception as e:
            print(f"[AUTO] Yahoo candidate {yc} failed: {e}")

    if _is_probably_crypto(symbol):
        for bc in _binance_candidates(symbol):
            try:
                df_b = fetch_binance(
                    bc, timeframe=timeframe, start=start, limit=limit)
                if not df_b.empty:
                    df_b.to_csv(csv_path, index=False)
                    print(
                        f"[AUTO] Binance OK → {bc} (rows={len(df_b)}) → {csv_path}")
                    return csv_path
            except Exception as e:
                print(f"[AUTO] Binance candidate {bc} failed: {e}")

    if not os.path.exists(csv_path):
        dummy = pd.DataFrame({
            "datetime": pd.date_range("2024-01-01", periods=200, freq="H", tz="UTC"),
            "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.5, "volume": 1000
        })
        dummy.to_csv(csv_path, index=False)
        print(f"[AUTO] WARNING: no data; created dummy {csv_path}")
    return csv_path
