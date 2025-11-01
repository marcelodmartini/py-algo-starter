# Python Algorithmic Trading Starter — Full Indicators Pack

This starter gives you a **production-ready scaffold** to build a realistic, robust algorithmic system in **Python**, focused on **entries and take-profits** with **many indicators** and **guardrails** to avoid overfitting.

## ✨ What you get
- **Backtrader** pipeline (backtest ready)
- **Feature engineering** with `pandas-ta` and `ta` (trend, momentum, volatility, volume, price-patterns)
- **Signal engine** with multi-indicator scoring
- **Risk manager** (ATR stops, trailing, time-stop, partial take-profit, kill-switch)
- **Walk-forward evaluation**
- **Metrics & reports** (CAGR, Sharpe/Sortino, PF, MaxDD) via `quantstats`
- **Config-driven** with `config.yaml`

> Bring your own OHLCV CSV or generate a **synthetic dataset** to test the wiring.

## 📦 Install
```bash
python -m venv .venv && source .venv/bin/activate   # (Linux/Mac)
pip install -r requirements.txt
```

## 🚀 Quickstart
```bash
python src/run_backtest.py --config config.yaml
```

- Drop your CSV in `data/your_asset.csv` with headers: `datetime,open,high,low,close,volume` (datetime ISO8601 or `%Y-%m-%d %H:%M:%S`). Update the path in `config.yaml`.
- Or first **generate synthetic data**:
```bash
python tools/make_synthetic_csv.py --symbol TEST --out data/TEST_1h.csv
```

## 🧩 Structure
```
py-algo-starter/
├── config.yaml
├── requirements.txt
├── README.md
├── data/
│   └── (put your CSVs here)
├── tools/
│   └── make_synthetic_csv.py
└── src/
    ├── indicators_pack.py
    ├── risk.py
    ├── signal_engine.py
    ├── strategy_bt.py
    ├── utils.py
    ├── walk_forward.py
    └── run_backtest.py
```

## 🧠 Indicators covered
- **Trend:** SMA, EMA, WMA, HMA, TEMA, Ichimoku, PSAR, SuperTrend, ADX/DMI, Vortex, Donchian, ChandeKroll, LinRegSlope
- **Momentum:** RSI, Stoch, StochRSI, MACD, PPO, ROC, CCI, MFI, Williams %R, Ultimate, TSI, divergences (option)
- **Volatility:** ATR, Bollinger, Keltner, DonchianWidth, ChaikinVol, HV, Parkinson, Beta, HV Ratio
- **Volume/Flow:** OBV, ADL, CMF, Ease of Movement, Volume Osc, VWAP/Anchored, VPT, NVI/PVI, RVOL
- **Price/Patterns:** Pivot Points, S/R dynamic, Fibonacci, Heikin-Ashi, Fractals, ZigZag, Gann H-L, Candle patterns
- **Stats/ML features:** rolling mean/std/skew/kurt, z-score, autocorr lags, returns/log-returns, percentile-in-range, PCA hooks, HMM regimes

## ⚠️ Notes
- The set is intentionally **broad**; use the config to **toggle** indicators and avoid overfitting.
- Start with a small **core set** and add more only if they **improve OOS** (walk-forward).

## 📜 License
MIT

---

## 🔄 Auto-Fetch de Datos (Binance/Yahoo)

Podés configurar **descarga automática** del histórico antes del backtest.

### Config
```yaml
data:
  csv_path: "data/BTCUSDT_1h.csv"
  auto_fetch: true           # 👈 activa descarga
  source: "crypto"           # "crypto" (ccxt) o "yahoo" (yfinance)
  symbol: "BTC/USDT"         # p.ej. BTC/USDT (crypto) o SPY (yahoo)
  exchange: "binance"        # solo crypto
  timeframe: "1H"            # crypto (se mapea a ccxt: 1H->1h)
  interval: "1h"             # yahoo
  start: "2022-01-01"        # opcional
  end: null
  limit: 5000                # crypto
```

Luego corré:
```bash
python src/run_backtest.py --config config.yaml
```
El runner llamará a `src/fetch_data.py` y guardará el CSV en `data/...` automáticamente.
