import backtrader as bt
import numpy as np

class IndicatorStrategy(bt.Strategy):
    params = dict(
        long_min_score=0.65,
        exit_score=0.40,
        stake_pct=0.98,
        atr_period=14,
        atr_stop_mult=2.0,
        atr_trail_mult=2.5,
        time_stop_bars=80,
        partial_tp=dict(enabled=True, tp1_rr=1.5, tp1_pct=0.5),
        printlog=False
    )

    def log(self, txt):
        if self.p.printlog:
            dt = self.datas[0].datetime.datetime(0)
            print(f"{dt.isoformat()} {txt}")

    def __init__(self):
        # Basic ATR for stops
        self.atr = bt.ind.ATR(self.datas[0], period=self.p.atr_period)

        # External scores are expected as data lines via "lines" or via PandasData feed with extra columns
        self.score_total = bt.indicators.Laguerre(self.datas[0].close)  # placeholder; will be replaced by custom line if provided

        self.order = None
        self.entry_bar = None
        self.entry_price = None
        self.highest_price = None
        self.partial_taken = False

    def next(self):
        if self.order:
            return

        close = self.data.close[0]
        atr = self.atr[0]

        # Get precomputed score from data (if available)
        score_total = getattr(self.data, "score_total", None)
        if score_total is not None:
            try:
                score_val = float(score_total[0])
            except Exception:
                score_val = 0.0
        else:
            score_val = 0.0

        if not self.position:
            if score_val >= self.p.long_min_score:
                stake = (self.broker.cash * self.p.stake_pct) / max(close, 1e-9)
                self.order = self.buy(size=stake)
                self.entry_bar = len(self)
                self.entry_price = close
                self.highest_price = close
                self.partial_taken = False
                self.p.stop_price = self.entry_price - self.p.atr_stop_mult * atr
                self.p.trail_price = self.entry_price - self.p.atr_trail_mult * atr
                self.log(f"BUY @ {close:.4f} (score={score_val:.2f})")
        else:
            # Update highest
            self.highest_price = max(self.highest_price, close)
            # Trailing stop
            trail = self.highest_price - self.p.atr_trail_mult * atr
            self.p.trail_price = max(self.p.trail_price, trail)

            # Partial take profit
            if self.p.partial_tp["enabled"] and not self.partial_taken:
                rr = (close - self.entry_price) / max((self.entry_price - self.p.stop_price), 1e-9)
                if rr >= self.p.partial_tp["tp1_rr"]:
                    self.order = self.sell(size=self.position.size * self.p.partial_tp["tp1_pct"])
                    self.partial_taken = True
                    self.log(f"PARTIAL TP @ {close:.4f} (RR={rr:.2f})")

            # Exit conditions
            exit_cond = False
            if score_val <= self.p.exit_score:
                exit_cond = True
                reason = "score_drop"
            elif close <= self.p.trail_price:
                exit_cond = True
                reason = "trailing_stop"
            elif (len(self) - self.entry_bar) >= self.p.time_stop_bars:
                exit_cond = True
                reason = "time_stop"

            if exit_cond:
                self.order = self.close()
                self.log(f"EXIT @ {close:.4f} ({reason})")
