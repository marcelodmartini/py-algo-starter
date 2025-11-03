import os
import pandas as pd
import yaml


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    # Override por variable de entorno (opcional)
    sym = os.getenv("SYMBOL")
    if sym:
        cfg.setdefault("data", {})
        cfg["data"]["symbol"] = sym.strip()

    return cfg


def read_csv(path: str, datetime_col: str, tz: str = "UTC") -> pd.DataFrame:
    df = pd.read_csv(path)
    if datetime_col in df.columns:
        df[datetime_col] = pd.to_datetime(
            df[datetime_col], utc=True).dt.tz_convert(tz)
    return df


def read_csv(path: str, datetime_col: str, tz: str = "UTC") -> pd.DataFrame:
    df = pd.read_csv(path)
    if datetime_col in df.columns:
        df[datetime_col] = pd.to_datetime(
            df[datetime_col], utc=True).dt.tz_convert(tz)
    return df


def resample_ohlcv(df, timeframe: str, datetime_col: str):
    df = df.copy()
    df = df.set_index(datetime_col).sort_index()
    rule = timeframe.lower()
    # Expect strings like "1h", "4h", "d"
    rule = rule.replace("1h", "1H").replace("4h", "4H").replace("d", "1D")
    o = df["open"].resample(rule).first()
    h = df["high"].resample(rule).max()
    l = df["low"].resample(rule).min()
    c = df["close"].resample(rule).last()
    v = df["volume"].resample(rule).sum()
    out = (pd.concat([o, h, l, c, v], axis=1).dropna().reset_index()
           .rename(columns={"index": "datetime"}))
    return out


def add_pct_change(df):
    df = df.copy()
    df["ret1"] = df["close"].pct_change()
    return df
