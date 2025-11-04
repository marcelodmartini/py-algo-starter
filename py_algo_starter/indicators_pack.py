import pandas as pd

def compute_indicators(df: pd.DataFrame, features: dict) -> pd.DataFrame:
    out = df.copy()
    # RSI simple
    if "rsi" in features:
        period = int(features["rsi"].get("period", 14))
        delta = out["close"].diff()
        up = delta.clip(lower=0).rolling(period).mean()
        down = -delta.clip(upper=0).rolling(period).mean()
        rs = up / (down.replace(0, 1e-9))
        out["rsi"] = 100 - (100 / (1 + rs))
    # EMAs
    if "ema" in features:
        fast = int(features["ema"].get("fast", 12))
        slow = int(features["ema"].get("slow", 26))
        out["ema_fast"] = out["close"].ewm(span=fast, adjust=False).mean()
        out["ema_slow"] = out["close"].ewm(span=slow, adjust=False).mean()
        out["ema_cross"] = (out["ema_fast"] > out["ema_slow"]).astype(float)
    # ATR (básico)
    if "atr" in features:
        n = int(features["atr"].get("period", 14))
        tr = (out["high"] - out["low"]).abs()
        tr2 = (out["high"] - out["close"].shift()).abs()
        tr3 = (out["low"] - out["close"].shift()).abs()
        tr = pd.concat([tr, tr2, tr3], axis=1).max(axis=1)
        out["atr"] = tr.rolling(n).mean()
    return out
