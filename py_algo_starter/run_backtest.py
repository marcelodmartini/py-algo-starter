from __future__ import annotations
import os
import pandas as pd
import numpy as np
import quantstats as qs
from .fetch_data import auto_fetch_to_csv
from .strategy_bt import run_bt
from .env import UploadClient

# Fuente limpia
import matplotlib as mpl
mpl.rcParams["font.family"] = "DejaVu Sans"

# === Indicadores ===


def ema(s, n): return s.ewm(span=n, adjust=False).mean()


def rsi(s, n=14):
    delta = s.diff()
    up, down = delta.clip(lower=0), -delta.clip(upper=0)
    rs = up.ewm(alpha=1/n).mean() / down.ewm(alpha=1/n).mean()
    return 100 - 100/(1+rs)


def macd(s, fast=12, slow=26, signal=9):
    m = ema(s, fast) - ema(s, slow)
    sline = ema(m, signal)
    return m, sline, m-sline

# === Inserción HTML ===


def color_emoji(v): return "🟢" if v == "LONG" else (
    "🔴" if v == "EXIT" else "🟡")


def inject_conclusion(html, bias, ep, enow, ex, table_html, symbol):
    box = f"""
<div style="border:2px solid #0a84ff;padding:10px;border-radius:10px;background:#f7faff;margin-bottom:12px">
<h2 style="color:#0a84ff;margin:0 0 6px 0">📊 Trade Conclusion - {symbol}</h2>
<p><b>Señal:</b> {color_emoji(bias)} {bias}</p>
<p><b>Entrada:</b> {ep or '-'} | <b>Actual:</b> {enow or '-'} | <b>Salida/Stop:</b> {ex or '-'}</p>
{table_html}
</div>"""
    if "<body" in html:
        i = html.find(">", html.find("<body"))
        html = html[:i+1] + box + html[i+1:]
    else:
        html = box + html
    return html

# === Pipeline ===


def run_once(symbol, cfg, out_html, upload=True):
    csv = auto_fetch_to_csv(cfg)
    df = pd.read_csv(csv, parse_dates=["datetime"]).sort_values("datetime")
    if len(df) < 30:
        return out_html

    df["ema20"] = ema(df["close"], 20)
    df["ema50"] = ema(df["close"], 50)
    df["rsi14"] = rsi(df["close"], 14)
    df["macd"], df["macd_signal"], df["macd_hist"] = macd(df["close"])

    last = df.iloc[-1]
    cond_long = (last.close > last.ema50) and (
        last.rsi14 > 50) and (last.macd > 0)
    cond_exit = (last.close < last.ema50) or (last.rsi14 < 45)
    bias = "LONG" if cond_long else ("EXIT" if cond_exit else "NEUTRAL")

    ep = round(last.ema20, 2)
    ex = round(last.ema50, 2)
    enow = round(last.close, 2)

    ret = df.set_index("datetime")["close"].pct_change().fillna(0)
    qs.extend_pandas()
    qs.reports.html(ret, output=out_html, title=f"{symbol} Backtest Report")

    # === Tabla semáforo ===
    recent = df.tail(
        10)[["datetime", "close", "ema20", "ema50", "rsi14", "macd"]]
    rows = ""
    for _, r in recent.iterrows():
        sig = "🟢" if (r.close > r.ema50 and r.rsi14 > 50) else (
            "🔴" if r.close < r.ema50 else "🟡")
        rows += f"<tr><td>{r.datetime.strftime('%Y-%m-%d')}</td><td>{r.close:.2f}</td><td>{r.ema20:.2f}</td><td>{r.ema50:.2f}</td><td>{r.rsi14:.1f}</td><td>{r.macd:.2f}</td><td>{sig}</td></tr>"
    table_html = f"""
<table border='1' cellspacing='0' cellpadding='4' style='border-collapse:collapse;font-size:12px;margin-top:8px'>
<tr style='background:#e0e7ff'><th>Fecha</th><th>Cierre</th><th>EMA20</th><th>EMA50</th><th>RSI</th><th>MACD</th><th>Señal</th></tr>
{rows}</table>"""

    # === Inserta la conclusión arriba del reporte ===
    with open(out_html, "r", encoding="utf-8") as f:
        html = f.read()
    html = inject_conclusion(html, bias, ep, enow, ex, table_html, symbol)
    with open(out_html, "w", encoding="utf-8") as f:
        f.write(html)

    if upload:
        try:
            client = UploadClient.from_env()
            client.upload_report(out_html)
        except Exception:
            pass

    return out_html
