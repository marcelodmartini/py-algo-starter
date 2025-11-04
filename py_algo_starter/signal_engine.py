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


def compute_entry_exit_advice(df):
    """Return dict with actionable advice based on SMA(50) and RSI(14).
    Requires df with columns: close, rsi_14 (if not present we'll compute a simple RSI).
    """
    import numpy as np
    import pandas as pd

    data = df.copy().dropna().tail(400)
    if data.empty or "close" not in data:
        return {"status": "no-data"}

    # SMA 50
    data["sma50"] = data["close"].rolling(50, min_periods=10).mean()

    # RSI 14 (compute if missing)
    if "rsi_14" not in data.columns:
        delta = data["close"].diff()
        gain = (delta.clip(lower=0)).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        rs = gain / (loss.replace(0, 1e-9))
        data["rsi_14"] = 100 - (100 / (1 + rs))

    last = data.iloc[-1]
    prev = data.iloc[-2] if len(data) > 1 else last

    signal = "HOLD"
    rationale = []
    entry_price = None
    exit_price = None

    # Bullish if close above SMA50 and RSI>55
    if last["close"] > last["sma50"] and last["rsi_14"] >= 55:
        signal = "BUY"
        entry_price = float(last["close"])
        rationale.append("Precio > SMA50 y RSI≥55")

    # Bearish if close below SMA50 or RSI<45
    if last["close"] < last["sma50"] or last["rsi_14"] <= 45:
        signal = "SELL" if signal != "BUY" else "TRIM"
        exit_price = float(last["close"])
        if last["close"] < last["sma50"]:
            rationale.append("Precio < SMA50")
        if last["rsi_14"] <= 45:
            rationale.append("RSI≤45")

    # Pivot S1/R1 from last daily bar approximation
    # We downsample to 1D if index is datetime-like
    try:
        daily = data["close"].resample("1D").agg(["first","max","min","last"]).dropna().tail(2)
        if len(daily) >= 2:
            H, L, C = daily.iloc[-2]["max"], daily.iloc[-2]["min"], daily.iloc[-2]["last"]
            pivot = (H+L+C)/3.0
            r1 = 2*pivot - L
            s1 = 2*pivot - H
        else:
            r1 = s1 = None
    except Exception:
        r1 = s1 = None

    return {
        "status": "ok",
        "signal": signal,
        "entry_price": entry_price,
        "exit_price": exit_price,
        "rationale": "; ".join(rationale) if rationale else "Señales neutrales",
        "r1": float(r1) if r1 is not None else None,
        "s1": float(s1) if s1 is not None else None,
    }


def render_advice_html(symbol, advice):
    if advice.get("status") != "ok":
        return "<section><h2>Señal</h2><p>No hay datos suficientes para una recomendación.</p></section>"
    def fmt(x):
        return "-" if x is None else f"{x:,.2f}"
    return f"""
<section style="border:1px solid #ddd;padding:12px;border-radius:10px;margin:16px 0">
  <h2 style="margin-top:0">📌 Señal para {symbol}</h2>
  <ul>
    <li><strong>Acción sugerida:</strong> {advice['signal']}</li>
    <li><strong>Nivel de entrada:</strong> {fmt(advice.get('entry_price'))}</li>
    <li><strong>Nivel de salida:</strong> {fmt(advice.get('exit_price'))}</li>
    <li><strong>S1 / R1 (pivots):</strong> {fmt(advice.get('s1'))} / {fmt(advice.get('r1'))}</li>
    <li><strong>Motivos:</strong> {advice.get('rationale','-')}</li>
  </ul>
</section>
"""
