import backtrader as bt

class IndicatorStrategy(bt.Strategy):
    params = dict(
        long_min_score=0.6,
        exit_score=0.2,
        stake_pct=0.2,
        atr_stop_mult=2.0,
        atr_trail_mult=1.5,
        time_stop_bars=200,
        partial_tp=dict(enabled=True, pct_1=0.5, rr_1=1.0),
        printlog=False,
    )

    def __init__(self):
        self.data_score = self.datas[0].score_total

    def next(self):
        if not self.position:
            if self.data_score[0] >= self.p.long_min_score:
                cash = self.broker.getcash()
                price = self.data.close[0]
                size = max(1, int((cash * self.p.stake_pct) / price))
                self.buy(size=size)
        else:
            if self.data_score[0] <= self.p.exit_score:
                self.close()
