import pandas as pd
import numpy as np

def walk_forward_splits(n_bars, train_bars=5000, test_bars=1000, rolling=True):
    i = 0
    out = []
    while True:
        start_train = i
        end_train = i + train_bars
        end_test = end_train + test_bars
        if end_test > n_bars: break
        out.append((start_train, end_train, end_test))
        i = i + (test_bars if rolling else end_test)
    return out
