from __future__ import annotations
import os
import pandas as pd
import numpy as np

# Evita warnings de fuentes en Matplotlib
try:
    import matplotlib as mpl
    mpl.rcParams["font.family"] = "DejaVu Sans"
except Exception:
    pass

import quantstats as qs

from .fetch_data import auto_fetch_to_csv
from .strategy_bt import run_bt
from .env import UploadClient


def _ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=n, adjust=False).mean()


def _rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    up = delta.clip(lower=0).ewm(alpha=1/period, adjust=False).mean()
    down = (-delta.clip(upper=0)).ewm(alpha=1/period, adjust=False).mean()
    rs = up / down.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def _macd(series: pd.Series, fast=12, slow=26, signal=9):
    ema_fast = _ema(series, fast)
    ema_slow = _ema(series, slow)
    macd = ema_fast - ema_slow
    sig = _ema(macd, signal)
    hist = macd - sig
    return macd, sig, hist


HTML_HEADER = """
<div style="border:2px solid #0a84ff;padding:12px;border-radius:10px;background:#f5f9ff;margin:8px 0 18px 0">
  <h2 style="margin:0 0 6px 0;color:#0a84ff">📌 Trade Conclusion</h2>
  <div style="font-size:14px;line-height:1.5">{body}</div>
</div>
"""


def _ensure_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "ema20" not in df.columns:
        df["ema20"] = _ema(df["close"], 20)
    if "ema50" not in df.columns:
        df["ema50"] = _ema(df["close"], 50)
    if "rsi14" not in df.columns and "rsi" not in df.columns:
        df["rsi14"] = _rsi(df["close"], 14)
    elif "rsi" in df.columns and "rsi14" not in df.columns:
        df["rsi14"] = df["rsi"]
    macd, sig, hist = _macd(df["close"])
    df["macd"] = macd
    df["macd_signal"] = sig
    df["macd_hist"] = hist
    return df


def _entry_exit_suggestion(df: pd.DataFrame) -> dict:
    last = df.iloc[-1]
    cond_long = (last.get("close", np.nan) > last.get("ema50", np.nan)) and (
        last.get("rsi14", 0) > 50) and (last.get("macd", 0) > 0)
    cond_exit = (last.get("close", np.nan) < last.get(
        "ema50", np.nan)) or (last.get("rsi14", 100) < 45)

    entry_price = float(last.get("ema20", np.nan))
    alt_now = float(last.get("close", np.nan))
    exit_price = float(last.get("ema50", np.nan))

    def r(x):
        if not np.isfinite(x):
            return None
        return float(np.round(x, 2 if x >= 10 else 4))

    return {
        "bias": "LONG" if cond_long and not cond_exit else ("EXIT/NEUTRAL" if cond_exit else "NEUTRAL"),
        "entry_price": r(entry_price),
        "entry_now": r(alt_now),
        "exit_price": r(exit_price)
    }


def inject_conclusion(report_html: str, advice: dict, symbol: str) -> str:
    if not advice:
        return report_html
    bias = advice["bias"]
    parts = []
    if bias == "LONG":
        parts.append(
            f"<b>Señal:</b> <span style='color:#0a0'>Comprar (tendencia alcista)</span> en <b>{symbol}</b>.")
        if advice["entry_price"]:
            parts.append(
                f"<b>Entrada sugerida:</b> zona de retroceso ≈ <code>{advice['entry_price']}</code> (EMA20). Alternativa: <code>{advice['entry_now']}</code> con confirmación.")
        else:
            parts.append(f"<b>Entrada sugerida:</b> {advice['entry_now']}.")
        parts.append(
            f"<b>Salida/Stop dinámico:</b> cierre bajo EMA50 ≈ <code>{advice['exit_price']}</code>.")
    elif bias == "EXIT/NEUTRAL":
        parts.append(
            f"<b>Señal:</b> <span style='color:#a00'>Salir / Neutral</span> en <b>{symbol}</b> (cierre bajo EMA50 o RSI&lt;45).")
        parts.append(
            f"<b>Salida sugerida:</b> próximo cierre bajo EMA50 ≈ <code>{advice['exit_price']}</code>.")
        parts.append(
            f"<b>Re-entrada:</b> sobre EMA50 recuperada + RSI&gt;50; ideal pullback a EMA20 ≈ <code>{advice['entry_price']}</code>.")
    else:
        parts.append(
            f"<b>Señal:</b> Neutral en <b>{symbol}</b>. Esperar cruce alcista EMA50 con RSI&gt;50 y MACD&gt;0.")
        parts.append(
            f"<b>Niveles guía:</b> Entrada ≈ EMA20 <code>{advice['entry_price']}</code>, Stop: EMA50 <code>{advice['exit_price']}</code>.")

    box = HTML_HEADER.format(body="<br/>".join(parts))
    if "<body" in report_html:
        i = report_html.find(">", report_html.find("<body"))
        if i != -1:
            return report_html[:i+1] + box + report_html[i+1:]
    return box + report_html


def run_once(symbol: str, cfg: dict, out_html: str, upload: bool = True) -> str:
    # 1) Fetch
    csv = auto_fetch_to_csv(cfg)

    # 2) Data + indicadores
    df = pd.read_csv(csv, parse_dates=["datetime"]).sort_values("datetime")
    df = _ensure_indicators(df)

    # 3) Returns para Quantstats
    try:
        ret, stats = run_bt(df)
        if ret is None or len(ret) == 0:
            ret = df.set_index("datetime")["close"].pct_change().fillna(0.0)
    except Exception:
        ret = df.set_index("datetime")["close"].pct_change().fillna(0.0)

    # 4) Reporte
    qs.extend_pandas()
    report_path = out_html
    qs.reports.html(ret, output=report_path,
                    title=f"Strategy Report - {symbol}")

    # 5) Conclusión de trade
    with open(report_path, "r", encoding="utf-8") as f:
        html = f.read()
    advice = _entry_exit_suggestion(df)
    html2 = inject_conclusion(html, advice, symbol)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html2)

    # 6) Upload
    if upload:
        try:
            client = UploadClient.from_env()
            client.upload_report(report_path)
        except Exception:
            pass
    return report_path
