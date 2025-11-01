import pandas as pd, numpy as np, yaml

def load_config(path="config.yaml"):
    with open(path, "r") as f:
        return yaml.safe_load(f)

def read_csv(path, datetime_col="datetime", tz="UTC"):
    df = pd.read_csv(path)
    df[datetime_col] = pd.to_datetime(df[datetime_col])
    if tz:
        df[datetime_col] = df[datetime_col].dt.tz_localize(tz, nonexistent='shift_forward', ambiguous='NaT', errors='ignore') if df[datetime_col].dt.tz is None else df[datetime_col]
    df = df.sort_values(datetime_col).reset_index(drop=True)
    return df

def resample_ohlcv(df, timeframe="1H", datetime_col="datetime"):
    df = df.set_index(datetime_col)
    o = df["open"].resample(timeframe).first()
    h = df["high"].resample(timeframe).max()
    l = df["low"].resample(timeframe).min()
    c = df["close"].resample(timeframe).last()
    v = df["volume"].resample(timeframe).sum()
    out = pd.concat([o,h,l,c,v], axis=1).dropna()
    out = out.reset_index()
    return out

def add_pct_change(df):
    df["ret"] = df["close"].pct_change().fillna(0.0)
    return df

def zscore(s, n=20):
    r = (s - s.rolling(n).mean()) / (s.rolling(n).std() + 1e-9)
    return r
