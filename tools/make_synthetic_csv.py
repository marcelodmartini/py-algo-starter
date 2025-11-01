import argparse, numpy as np, pandas as pd
from datetime import datetime, timedelta

def make_series(n=5000, start="2023-01-01 00:00:00", tf_minutes=60, seed=42):
    rng = np.random.default_rng(seed)
    dt0 = pd.to_datetime(start)
    idx = [dt0 + pd.Timedelta(minutes=tf_minutes*i) for i in range(n)]
    # Geometric Brownian Motion + seasonal component
    price = 100 * np.exp(np.cumsum((0.0002 + 0.01*rng.standard_normal(n))))
    price *= (1 + 0.02*np.sin(np.linspace(0, 20*np.pi, n)))
    close = price
    high = close * (1 + 0.002*rng.random(n))
    low = close * (1 - 0.002*rng.random(n))
    openp = (high + low) / 2
    vol = (1e4 * (1 + 0.5*rng.random(n))).astype(int)
    df = pd.DataFrame({"datetime": idx, "open": openp, "high": high, "low": low, "close": close, "volume": vol})
    return df

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default="TEST")
    ap.add_argument("--out", default="data/TEST_1h.csv")
    ap.add_argument("--bars", type=int, default=6000)
    ap.add_argument("--tf", default="1H", choices=["1min","5min","15min","1H","4H","1D"])
    args = ap.parse_args()

    tf_map = {"1min":1,"5min":5,"15min":15,"1H":60,"4H":240,"1D":1440}
    df = make_series(n=args.bars, tf_minutes=tf_map[args.tf])
    df.to_csv(args.out, index=False)
    print(f"Saved synthetic OHLCV to {args.out}")

if __name__ == "__main__":
    main()
