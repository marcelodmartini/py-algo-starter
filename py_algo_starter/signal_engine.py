import pandas as pd

def compute_signal_scores(df: pd.DataFrame, weights: dict) -> pd.DataFrame:
    out = df.copy()
    # Señales normalizadas muy simples de ejemplo
    s_rsi = (out.get("rsi") - 50).abs().fillna(0) / 50.0  # 0..1
    s_ema = out.get("ema_cross", 0).fillna(0)              # 0 or 1
    s_atr = (out.get("atr").pct_change().abs().fillna(0)).clip(0, 1)
    w_rsi = float(weights.get("rsi", 0))
    w_ema = float(weights.get("ema_cross", 0))
    w_atr = float(weights.get("atr_trend", 0))
    out["score_total"] = (w_rsi * s_rsi) + (w_ema * s_ema) + (w_atr * s_atr)
    return out
