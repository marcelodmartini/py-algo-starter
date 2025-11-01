import numpy as np
import pandas as pd

class RiskManager:
    def __init__(self, atr_mult_stop=2.0, atr_mult_trail=2.5, time_stop_bars=80, partial_tp=None):
        self.atr_mult_stop = atr_mult_stop
        self.atr_mult_trail = atr_mult_trail
        self.time_stop_bars = time_stop_bars
        self.partial_tp = partial_tp or {"enabled": True, "tp1_rr": 1.5, "tp1_pct": 0.5}

    def initial_stop(self, entry_price, atr):
        return entry_price - self.atr_mult_stop * atr

    def trailing_stop(self, highest_price, atr):
        return highest_price - self.atr_mult_trail * atr
