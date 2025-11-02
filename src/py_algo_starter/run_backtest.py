import argparse
import os
from pathlib import Path
import pandas as pd
import backtrader as bt
import quantstats as qs
import requests

# Imports que funcionan si el proyecto está como paquete o como módulos sueltos
try:
    from .utils import load_config, read_csv, resample_ohlcv, add_pct_change
    from .indicators_pack import compute_indicators
    from .fetch_data import auto_fetch_to_csv
    from .signal_engine import compute_signal_scores
    from .strategy_bt import IndicatorStrategy
except Exception:
    from utils import load_config, read_csv, resample_ohlcv, add_pct_change
    from indicators_pack import compute_indicators
    from fetch_data import auto_fetch_to_csv
    from signal_engine import compute_signal_scores
    from strategy_bt import IndicatorStrategy

WEB_SERVICE_BASE_URL = os.getenv("WEB_SERVICE_BASE_URL", "").rstrip("/")
UPLOAD_TOKEN = os.getenv("UPLOAD_TOKEN", "")
REPORTS_DIR = os.getenv("REPORTS_DIR", "/tmp/reports")


class PandasDataExt(bt.feeds.PandasData):
    lines = ('score_total',)
    params = (
        ('datetime', None),
        ('open', 'open'),
        ('high', 'high'),
        ('low', 'low'),
        ('close', 'close'),
        ('volume', 'volume'),
        ('openinterest', None),
        ('score_total', 'score_total'),
    )


def _upload_report(report_path: str, filename: str = "report.html"):
    if not WEB_SERVICE_BASE_URL or not UPLOAD_TOKEN:
        print("[WARN] Sin WEB_SERVICE_BASE_URL o UPLOAD_TOKEN — no se sube el reporte.")
        return None
    url = f"{WEB_SERVICE_BASE_URL}/upload-report"
    # Aceptamos ambos headers del lado servidor; usamos X-Upload-Token aquí
    headers = {"X-Upload-Token": UPLOAD_TOKEN}
    files = {"file": (filename, open(report_path, "rb"), "text/html")}
    print(f"[INFO] Subiendo reporte a {url} ...")
    try:
        import json
        r = requests.post(url, headers=headers, files=files, timeout=60)
        r.raise_for_status()
        data = r.json()
        print("[OK] Reporte subido ✅")
        if isinstance(data, dict) and data.get("url"):
            u = data["url"]
            return u if u.startswith("http") else f"{WEB_SERVICE_BASE_URL}{u}"
        return f"{WEB_SERVICE_BASE_URL}/reports/{filename}"
    except Exception as e:
        print(f"[ERROR] Falló la subida del reporte: {e}")
        return None


def run_once(config_path: str = "config.yaml"):
    """Ejecuta 1 backtest y devuelve (ruta_html_local, url_publica|None)."""
    cfg = load_config(config_path)
    csv_auto = auto_fetch_to_csv(cfg)
    df = read_csv(csv_auto, cfg["data"]["datetime_col"], cfg["data"]["tz"])
    df = resample_ohlcv(df, cfg["data"]["timeframe"], cfg["data"]["datetime_col"])
    df = add_pct_change(df)
    df = compute_indicators(df, cfg["features"])
    df = compute_signal_scores(df, cfg["signals"]["weights"])

    df = df.dropna().reset_index(drop=True)

    cerebro = bt.Cerebro()
    cerebro.addstrategy(
        IndicatorStrategy,
        long_min_score=cfg["signals"]["thresholds"]["long_min_score"],
        exit_score=cfg["signals"]["thresholds"]["exit_score"],
        stake_pct=cfg["backtest"]["stake_pct"],
        atr_stop_mult=cfg["risk"]["atr_stop_mult"],
        atr_trail_mult=cfg["risk"]["atr_trail_mult"],
        time_stop_bars=cfg["risk"]["time_stop_bars"],
        partial_tp=cfg["risk"]["partial_tp"],
        printlog=cfg["backtest"]["printlog"],
    )

    data = df.copy()
    data.set_index("datetime", inplace=True)
    feed = PandasDataExt(dataname=data)
    cerebro.adddata(feed)

    cerebro.broker.setcash(cfg["backtest"]["cash"])
    cerebro.broker.setcommission(commission=cfg["backtest"]["commission"])

    cerebro.run()
    value = cerebro.broker.getvalue()
    print(f"Final Portfolio Value: {value:.2f}")

    Path(REPORTS_DIR).mkdir(parents=True, exist_ok=True)
    report_path = os.path.join(REPORTS_DIR, "report.html")

    ret = data["close"].pct_change().fillna(0.0)
    qs.reports.html(ret, output=report_path, title="Strategy Report")
    print(f"[OK] Reporte generado en: {report_path}")

    public_url = _upload_report(report_path, "report.html")
    if public_url:
        print(f"[INFO] Reporte público: {public_url}")

    return report_path, public_url


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    args = ap.parse_args()
    run_once(args.config)


if __name__ == "__main__":
    main()
