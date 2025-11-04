# -*- coding: utf-8 -*-
from __future__ import annotations
import pandas as pd
import datetime as dt
try:
    import yfinance as yf
except Exception:
    yf = None

from .symbols import is_crypto_symbol, normalize_for_yahoo, normalize_for_exchange

# Config por defecto para YF en 1h: usar period si no hay start/end
_DEFAULT_PERIOD_BY_INTERVAL = {
    "1h": "60d",
    "30m": "30d",
    "15m": "30d",
    "1d": "3y",
}


def _yf_download(ticker: str, interval: str, start=None, end=None, period=None) -> pd.DataFrame:
    kwargs = dict(
        interval=interval,
        progress=False,
        auto_adjust=False,  # consistente con OHLC para pivots/EMA
    )
    if start and not period:
        kwargs["start"] = start
    if end:
        kwargs["end"] = end
    if period and not start:
        kwargs["period"] = period
    df = yf.download(ticker, **kwargs)
    if df is None or df.empty:
        return pd.DataFrame()
    df = df.rename(columns=str.lower)
    df.index = pd.to_datetime(df.index)
    # YF algunos símbolos traen 'adj close'; conservar 'close'
    return df[["open", "high", "low", "close", "volume"]].dropna(how="any")


def fetch_ohlcv(symbol: str, interval: str = "1h", start: str | None = None, end: str | None = None) -> pd.DataFrame:
    """
    Retorna OHLCV con index datetime.
    - Para EQUITY/ETF => Yahoo (AAPL, SPY)
    - Para CRYPTO => Yahoo (BTC-USD/ETH-USD) por ahora. (Evitar Binance 451)
    """
    if yf is None:
        raise RuntimeError("yfinance no está instalado en el entorno")

    # Normalizar para Yahoo
    yf_symbol = normalize_for_yahoo(symbol)

    # Elegir period por defecto si no pasás start
    period = None
    if start is None:
        period = _DEFAULT_PERIOD_BY_INTERVAL.get(interval, None)

    df = _yf_download(yf_symbol, interval=interval,
                      start=start, end=end, period=period)

    return df


def fetch_and_validate(symbol: str, interval: str = "1h", start: str | None = None, end: str | None = None) -> pd.DataFrame:
    df = fetch_ohlcv(symbol, interval=interval, start=start, end=end)
    # filtrar duplicados y asegurar sort
    df = df[~df.index.duplicated(keep="last")].sort_index()
    return df
