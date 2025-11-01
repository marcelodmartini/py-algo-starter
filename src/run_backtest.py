import argparse, os
import pandas as pd
import backtrader as bt
import quantstats as qs

from utils import load_config, read_csv, resample_ohlcv, add_pct_change
from indicators_pack import compute_indicators
from fetch_data import auto_fetch_to_csv
from signal_engine import compute_signal_scores
from strategy_bt import IndicatorStrategy

class PandasDataExt(bt.feeds.PandasData):
    lines = ('score_total',)
    params = (('datetime', None),
              ('open', 'open'),
              ('high', 'high'),
              ('low', 'low'),
              ('close', 'close'),
              ('volume', 'volume'),
              ('openinterest', None),
              ('score_total', 'score_total'))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    args = ap.parse_args()

    cfg = load_config(args.config)
    csv_auto = auto_fetch_to_csv(cfg)
    df = read_csv(csv_auto, cfg["data"]["datetime_col"], cfg["data"]["tz"])
    df = resample_ohlcv(df, cfg["data"]["timeframe"], cfg["data"]["datetime_col"])
    df = add_pct_change(df)
    df = compute_indicators(df, cfg["features"])
    df = compute_signal_scores(df, cfg["signals"]["weights"])

    # Drop NaNs
    df = df.dropna().reset_index(drop=True)

    cerebro = bt.Cerebro()
    cerebro.addstrategy(IndicatorStrategy,
                        long_min_score=cfg["signals"]["thresholds"]["long_min_score"],
                        exit_score=cfg["signals"]["thresholds"]["exit_score"],
                        stake_pct=cfg["backtest"]["stake_pct"],
                        atr_stop_mult=cfg["risk"]["atr_stop_mult"],
                        atr_trail_mult=cfg["risk"]["atr_trail_mult"],
                        time_stop_bars=cfg["risk"]["time_stop_bars"],
                        partial_tp=cfg["risk"]["partial_tp"],
                        printlog=cfg["backtest"]["printlog"])

    data = df.copy()
    data.set_index("datetime", inplace=True)
    feed = PandasDataExt(dataname=data)

    cerebro.adddata(feed)
    cerebro.broker.setcash(cfg["backtest"]["cash"])
    cerebro.broker.setcommission(commission=cfg["backtest"]["commission"])

    result = cerebro.run()
    value = cerebro.broker.getvalue()
    print(f"Final Portfolio Value: {value:.2f}")

    # Basic returns series for QuantStats
    # Note: Backtrader doesn't expose per-bar PnL easily without analyzers; we compute naive returns from close
    ret = data["close"].pct_change().fillna(0.0)
    qs.reports.html(ret, output="report.html", title="Strategy Report")

if __name__ == "__main__":
    main()
