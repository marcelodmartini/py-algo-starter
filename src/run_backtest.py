# src/run_backtest.py
import argparse
import os
from pathlib import Path
import pandas as pd
import backtrader as bt
import quantstats as qs
import requests

from utils import load_config, read_csv, resample_ohlcv, add_pct_change
from indicators_pack import compute_indicators
from fetch_data import auto_fetch_to_csv
from signal_engine import compute_signal_scores
from strategy_bt import IndicatorStrategy

# 🔹 ENV VARS para integrarse con el Web Service
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


def upload_report(report_path: str, filename: str = "report.html") -> str | None:
    """
    Sube el reporte HTML al Web Service FastAPI (py-algo-web-service)
    usando el endpoint POST /upload-report. Devuelve la URL pública.
    """
    if not WEB_SERVICE_BASE_URL or not UPLOAD_TOKEN:
        print("[WARN] Falta WEB_SERVICE_BASE_URL o UPLOAD_TOKEN — omito upload.")
        return None

    url = f"{WEB_SERVICE_BASE_URL}/upload-report"
    headers = {"X-Upload-Token": UPLOAD_TOKEN}

    print(f"[INFO] Subiendo reporte a {url} ...")
    try:
        with open(report_path, "rb") as fh:
            files = {"file": (filename, fh, "text/html")}
            r = requests.post(url, headers=headers, files=files, timeout=60)
            r.raise_for_status()
        data = r.json() if r.headers.get("content-type",
                                         "").startswith("application/json") else {}
        public_url = data.get(
            "url") or f"{WEB_SERVICE_BASE_URL}/report/{filename}"
        print("[OK] Reporte subido correctamente ✅")
        return public_url
    except Exception as e:
        print(f"[ERROR] Falló la subida del reporte: {e}")
        return None


def run_once(config_path: str = "config.yaml") -> tuple[str, str | None]:
    """
    Ejecuta el backtest 1 vez, genera QuantStats HTML en REPORTS_DIR y (si hay config)
    lo sube al Web Service. Devuelve (report_path_local, public_url|None).
    """
    cfg = load_config(config_path)

    # 1) Data pipeline
    csv_auto = auto_fetch_to_csv(cfg)
    df = read_csv(csv_auto, cfg["data"]["datetime_col"], cfg["data"]["tz"])
    df = resample_ohlcv(df, cfg["data"]["timeframe"],
                        cfg["data"]["datetime_col"])
    df = add_pct_change(df)
    df = compute_indicators(df, cfg["features"])
    df = compute_signal_scores(df, cfg["signals"]["weights"])
    df = df.dropna().reset_index(drop=True)

    # 2) Backtrader
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
    print(f"[INFO] Final Portfolio Value: {value:.2f}")

    # 3) QuantStats → HTML
    Path(REPORTS_DIR).mkdir(parents=True, exist_ok=True)
    report_path = os.path.join(REPORTS_DIR, "report.html")
    ret = data["close"].pct_change().fillna(0.0)
    qs.reports.html(ret, output=report_path, title="Strategy Report")
    print(f"[OK] Reporte generado en: {report_path}")

    # 4) Upload opcional al Web Service
    public_url = upload_report(report_path)

    return report_path, public_url


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    args = ap.parse_args()

    report_path, url = run_once(args.config)
    print(f"[DONE] HTML local: {report_path}")
    if url:
        print(f"[DONE] URL pública: {url}")


if __name__ == "__main__":
    main()
