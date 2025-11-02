import argparse
import os
from pathlib import Path
import backtrader as bt
import quantstats as qs
import requests

from .utils import load_config, read_csv, resample_ohlcv, add_pct_change
from .indicators_pack import compute_indicators
from .fetch_data import auto_fetch_to_csv
from .signal_engine import compute_signal_scores
from .strategy_bt import IndicatorStrategy
from .env import WEB_SERVICE_BASE_URL, UPLOAD_TOKEN, REPORTS_DIR


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
    """
    Sube el HTML al web-service (endpoint /upload-report).
    Intenta leer data['url'] del JSON de respuesta y,
    si no existe, hace fallback a /reports/<filename>.
    """
    if not WEB_SERVICE_BASE_URL or not UPLOAD_TOKEN:
        print("[WARN] No WEB_SERVICE_BASE_URL/UPLOAD_TOKEN — skip upload")
        return None

    url = f"{WEB_SERVICE_BASE_URL.rstrip('/')}/upload-report"
    headers = {"X-Upload-Token": UPLOAD_TOKEN}

    try:
        with open(report_path, "rb") as fh:
            files = {"file": (filename, fh, "text/html")}
            r = requests.post(url, headers=headers, files=files, timeout=60)
        r.raise_for_status()

        try:
            data = r.json()
        except Exception:
            data = {}

        if isinstance(data, dict):
            # Soporta ambas variantes del server:
            # 1) {"filename": "...", "url": "..."}
            # 2) {"ok": True, "saved": ["/reports/report-....html", "/"]}
            if data.get("url"):
                return data["url"]
            saved = data.get("saved")
            if isinstance(saved, list) and saved:
                # primera entrada suele ser el path del histórico
                first = saved[0]
                if isinstance(first, str) and first.startswith("/"):
                    return f"{WEB_SERVICE_BASE_URL.rstrip('/')}{first}"

        # Fallback genérico
        return f"{WEB_SERVICE_BASE_URL.rstrip('/')}/reports/{filename}"
    except Exception as e:
        print(f"[ERROR] upload failed: {e}")
        return None


def run_once(config_path: str = "config.yaml"):
    """
    Ejecuta el pipeline completo:
      - fetch/resample/indicadores/señales
      - backtest con Backtrader
      - genera QuantStats HTML en REPORTS_DIR
      - intenta subir el reporte al web-service
    Devuelve: (report_path_local, public_url_o_None)
    """
    cfg = load_config(config_path)

    csv_auto = auto_fetch_to_csv(cfg)
    df = read_csv(csv_auto, cfg["data"]["datetime_col"], cfg["data"]["tz"])
    df = resample_ohlcv(df, cfg["data"]["timeframe"],
                        cfg["data"]["datetime_col"])
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

    # Generar reporte HTML
    Path(REPORTS_DIR).mkdir(parents=True, exist_ok=True)
    filename = "report.html"
    report_path = os.path.join(REPORTS_DIR, filename)

    # De momento usamos retornos simples de close; si querés PnL real, luego
    # agregamos Analyzer y construimos la serie de returns de la equity curve.
    ret = data["close"].pct_change().fillna(0.0)
    qs.reports.html(ret, output=report_path, title="Strategy Report")

    # Subir al web-service (opcional)
    public_url = _upload_report(report_path, filename)
    return report_path, public_url


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    args = ap.parse_args()
    path, url = run_once(args.config)
    print(f"[OK] Report: {path}")
    if url:
        print(f"[OK] Public URL: {url}")


if __name__ == "__main__":
    main()
