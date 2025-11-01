import numpy as np
import pandas as pd

def _score_trend(row):
    s = 0.0; c = 0
    # Example trend features
    for k in ["ema_12","ema_26","ema_50","ema_200","sma_20","sma_50","sma_200","adx","supertrend"]:
        if k in row and not pd.isna(row[k]):
            if k.startswith(("ema","sma")):
                s += (1.0 if row["close"] > row[k] else 0.0); c += 1
            elif k == "adx":
                s += (1.0 if row[k] > 20 else 0.0); c += 1
            elif k == "supertrend":
                s += (1.0 if row["close"] > row[k] else 0.0); c += 1
    return s / max(c,1)

def _score_momentum(row):
    s = 0.0; c = 0
    for k in ["rsi_14","macd","macd_hist","stoch_k_14","stochrsi_14","roc_10","tsi"]:
        if k in row and not pd.isna(row[k]):
            if k.startswith("rsi"):
                s += (1.0 if 50 <= row[k] <= 70 else (0.5 if row[k] > 70 else 0.0)); c += 1
            elif k in ["macd","macd_hist","tsi","roc_10"]:
                s += (1.0 if row[k] > 0 else 0.0); c += 1
            elif k.startswith("stoch"):
                s += (1.0 if row[k] > 50 else 0.0); c += 1
    return s / max(c,1)

def _score_volatility(row):
    s = 0.0; c = 0
    for k in ["atr_14","bb_low_20","bb_high_20"]:
        if k in row and not pd.isna(row[k]):
            if k == "atr_14":
                # Prefer moderate volatility: normalize via rolling
                s += 0.5; c += 1
            elif k == "bb_low_20":
                s += (1.0 if row["close"] > row[k] else 0.0); c += 1
            elif k == "bb_high_20":
                s += (0.0 if row["close"] > row[k] else 1.0); c += 1
    return s / max(c,1)

def _score_volume(row):
    s = 0.0; c = 0
    for k in ["obv","cmf_20","vpt","rvol_20"]:
        if k in row and not pd.isna(row[k]):
            if k == "cmf_20":
                s += (1.0 if row[k] > 0 else 0.0); c += 1
            elif k in ["obv","vpt","rvol_20"]:
                s += 0.5; c += 1  # simplified; replace with slopes/thresholds
    return s / max(c,1)

def _score_patterns(row):
    s = 0.0; c = 0
    for k in ["bullish_engulfing","fractal_bull"]:
        if k in row and not pd.isna(row[k]):
            s += float(row[k] > 0); c += 1
    return s / max(c,1)

def _score_stats(row):
    s = 0.0; c = 0
    for k in ["zscore_20","ret_1"]:
        if k in row and not pd.isna(row[k]):
            if k.startswith("zscore"):
                s += (1.0 if -1.0 <= row[k] <= 1.0 else 0.2); c += 1
            else:
                s += (1.0 if row[k] > 0 else 0.0); c += 1
    return s / max(c,1)

def compute_signal_scores(df: pd.DataFrame, weights: dict):
    w_tr = weights.get("trend", 0.3)
    w_mo = weights.get("momentum", 0.25)
    w_vo = weights.get("volatility", 0.1)
    w_vf = weights.get("volume_flow", 0.15)
    w_pp = weights.get("price_patterns", 0.1)
    w_st = weights.get("stats_ml", 0.1)

    scores = []
    for _, row in df.iterrows():
        tr = _score_trend(row)
        mo = _score_momentum(row)
        vo = _score_volatility(row)
        vf = _score_volume(row)
        pp = _score_patterns(row)
        st = _score_stats(row)
        total = (w_tr*tr + w_mo*mo + w_vo*vo + w_vf*vf + w_pp*pp + w_st*st) / max((w_tr+w_mo+w_vo+w_vf+w_pp+w_st),1e-9)
        scores.append((tr,mo,vo,vf,pp,st,total))
    out = pd.DataFrame(scores, columns=["score_trend","score_momentum","score_volatility","score_volume","score_patterns","score_stats","score_total"])
    return pd.concat([df.reset_index(drop=True), out], axis=1)
