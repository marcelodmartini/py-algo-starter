import pandas as pd
import numpy as np
import pandas_ta as ta

# Helper to safely add columns (avoid collisions)
def _add(df, name, ser):
    if isinstance(ser, pd.Series):
        df[name] = ser
    elif isinstance(ser, pd.DataFrame):
        for col in ser.columns:
            df[f"{name}_{col}"] = ser[col]
    return df

def compute_indicators(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    close = df["close"]
    high = df["high"]
    low  = df["low"]
    vol  = df["volume"]

    # --- Trend ---
    trend = cfg.get("trend", {})
    for n in trend.get("sma", []):
        _add(df, f"sma_{n}", ta.sma(close, length=n))
    for n in trend.get("ema", []):
        _add(df, f"ema_{n}", ta.ema(close, length=n))
    for n in trend.get("wma", []):
        _add(df, f"wma_{n}", ta.wma(close, length=n))
    for n in trend.get("hma", []):
        _add(df, f"hma_{n}", ta.hma(close, length=n))
    for n in trend.get("tema", []):
        _add(df, f"tema_{n}", ta.tema(close, length=n))

    if trend.get("ichimoku", False):
        ichi = ta.ichimoku(high, low, close)
        # pandas-ta returns tuple of (conversion, base, spanA, spanB, lagging)
        if isinstance(ichi, tuple) and len(ichi) >= 2:
            conv = ichi[0]; base = ichi[1]; spanA = ichi[2]; spanB = ichi[3]
            _add(df, "ichi_conv", conv)
            _add(df, "ichi_base", base)
            _add(df, "ichi_spanA", spanA)
            _add(df, "ichi_spanB", spanB)

    if trend.get("psar", False):
        _add(df, "psar", ta.psar(high, low, close)["PSARl_0.02_0.2"])

    sup = trend.get("supertrend", {})
    if sup and sup.get("enabled", False):
        st = ta.supertrend(high, low, close, length=sup.get("length",10), multiplier=sup.get("multiplier",3.0))
        _add(df, "supertrend", st["SUPERT_10_3.0"] if "SUPERT_10_3.0" in st else st.iloc[:,0])

    if trend.get("adx_dmi", False):
        dmi = ta.adx(high, low, close)
        _add(df, "adx", dmi["ADX_14"] if "ADX_14" in dmi else dmi.iloc[:,0])
        _add(df, "di_pos", dmi.filter(like="DMP_").iloc[:,0])
        _add(df, "di_neg", dmi.filter(like="DMN_").iloc[:,0])

    if trend.get("vortex", False):
        vi = ta.vortex(high, low, close)
        _add(df, "vortex_pos", vi.iloc[:,0])
        _add(df, "vortex_neg", vi.iloc[:,1])

    for n in trend.get("donchian", []):
        don = ta.donchian(high, low, lower_length=n, upper_length=n)
        _add(df, f"donch_mid_{n}", don["DCL_{}_{}".format(n,n)].rolling(1).mean())

    if trend.get("chande_kroll", False):
        ck = ta.cksp(high, low, close)
        _add(df, "chande_kroll", ck.iloc[:,0])

    for n in trend.get("linreg_slope", []):
        _add(df, f"linreg_slope_{n}", ta.linreg(close, length=n))

    # --- Momentum ---
    mom = cfg.get("momentum", {})
    for n in mom.get("rsi", []):
        _add(df, f"rsi_{n}", ta.rsi(close, length=n))
    for n in mom.get("stoch", []):
        st = ta.stoch(high, low, close, k=n, d=3, smooth_k=3)
        _add(df, f"stoch_k_{n}", st["STOCHk_{}_3_3".format(n)] if f"STOCHk_{n}_3_3" in st else st.iloc[:,0])
        _add(df, f"stoch_d_{n}", st["STOCHd_{}_3_3".format(n)] if f"STOCHd_{n}_3_3" in st else st.iloc[:,1])
    for n in mom.get("stochrsi", []):
        _add(df, f"stochrsi_{n}", ta.stochrsi(close, length=n))
    macd_cfg = mom.get("macd", {"fast":12,"slow":26,"signal":9})
    if macd_cfg:
        macd = ta.macd(close, fast=macd_cfg["fast"], slow=macd_cfg["slow"], signal=macd_cfg["signal"])
        _add(df, "macd", macd["MACD_12_26_9"] if "MACD_12_26_9" in macd else macd.iloc[:,0])
        _add(df, "macd_signal", macd.filter(like="MACDs_").iloc[:,0])
        _add(df, "macd_hist", macd.filter(like="MACDh_").iloc[:,0])
    if mom.get("ppo", False):
        _add(df, "ppo", ta.ppo(close))
    for n in mom.get("roc", []):
        _add(df, f"roc_{n}", ta.roc(close, length=n))
    for n in mom.get("cci", []):
        _add(df, f"cci_{n}", ta.cci(high, low, close, length=n))
    for n in mom.get("mfi", []):
        _add(df, f"mfi_{n}", ta.mfi(high, low, close, vol, length=n))
    for n in mom.get("williams_r", []):
        _add(df, f"williams_r_{n}", ta.willr(high, low, close, length=n))
    if mom.get("ultimate", False):
        _add(df, "ultimate", ta.uo(high, low, close))
    if mom.get("tsi", False):
        _add(df, "tsi", ta.tsi(close))

    # --- Volatility ---
    vol = cfg.get("volatility", {})
    for n in vol.get("atr", []):
        _add(df, f"atr_{n}", ta.atr(high, low, close, length=n))
    for n in vol.get("bollinger", []):
        bb = ta.bbands(close, length=n)
        _add(df, f"bb_high_{n}", bb["BBU_{}".format(n)] if f"BBU_{n}" in bb else bb.iloc[:,0])
        _add(df, f"bb_low_{n}",  bb["BBL_{}".format(n)] if f"BBL_{n}" in bb else bb.iloc[:,2])
        _add(df, f"bb_mid_{n}",  bb["BBM_{}".format(n)] if f"BBM_{n}" in bb else bb.iloc[:,1])
    for n in vol.get("keltner", []):
        k = ta.kc(high, low, close, length=n)
        _add(df, f"keltner_h_{n}", k.iloc[:,0])
        _add(df, f"keltner_l_{n}", k.iloc[:,1])
        _add(df, f"keltner_m_{n}", k.iloc[:,2])
    for n in vol.get("donch_width", []):
        dc = ta.donchian(high, low, lower_length=n, upper_length=n)
        width = (dc.iloc[:,1] - dc.iloc[:,0]) / (dc.iloc[:,2].rolling(n).mean() + 1e-9)
        _add(df, f"donch_width_{n}", width)
    if vol.get("chaikin_vol", False):
        _add(df, "chaikin_vol", ta.cvol(high, low))
    for n in vol.get("hv", []):
        _add(df, f"hv_{n}", ta.hvol(close, length=n))
    if vol.get("parkinson", False):
        # Parkinson volatility approximation (using pandas-ta range percent)
        _add(df, "parkinson_vol", ta.rvi(high, low, close))
    for n in vol.get("hv_ratio", []):
        hv = ta.hvol(close, length=n)
        hv_ma = hv.rolling(n).mean()
        _add(df, f"hv_ratio_{n}", hv / (hv_ma+1e-9))

    # --- Volume / Flow ---
    volf = cfg.get("volume_flow", {})
    if volf.get("obv", False):
        _add(df, "obv", ta.obv(close, df["volume"]))
    if volf.get("adl", False):
        _add(df, "adl", ta.adl(high, low, close, df["volume"]))
    for n in volf.get("cmf", []):
        _add(df, f"cmf_{n}", ta.cmf(high, low, close, df["volume"], length=n))
    if volf.get("ease_of_move", False):
        _add(df, "ease_of_move", ta.eom(high, low, df["volume"]))
    if volf.get("volume_osc", False):
        _add(df, "volume_osc", ta.vo(df["volume"]))
    if volf.get("vwap", False):
        _add(df, "vwap", ta.vwap(high, low, close, df["volume"]))
    avwap = volf.get("anchored_vwap", {"enabled": False})
    if avwap and avwap.get("enabled", False):
        # For simplicity: compute since anchor date (requires filtering)
        pass
    if volf.get("vpt", False):
        _add(df, "vpt", ta.vpt(close, df["volume"]))
    if volf.get("nvi_pvi", False):
        _add(df, "nvi", ta.nvi(close, df["volume"]))
        _add(df, "pvi", ta.pvi(close, df["volume"]))
    for n in volf.get("rvol", []):
        vol = df["volume"]
        _add(df, f"rvol_{n}", vol / (vol.rolling(n).mean() + 1e-9))

    # --- Price / Patterns ---
    patt = cfg.get("price_patterns", {})
    if patt.get("heikin_ashi", False):
        ha = ta.ha(high, low, df["open"], close)
        _add(df, "ha_close", ha["HA_close"] if "HA_close" in ha else ha.iloc[:,3])
    if patt.get("fractals", False):
        fr = ta.fractals(high, low)
        _add(df, "fractal_bull", fr.iloc[:,0])
        _add(df, "fractal_bear", fr.iloc[:,1])
    if (z := patt.get("zigzag_pct", 0)) and z > 0:
        # Simple ZigZag approximation via pandas-ta
        zz = ta.zigzag(high, low, percent=z)
        _add(df, "zigzag", zz)
    if patt.get("pivots", False):
        pp = ta.pivots(high, low, close, show=True)
        _add(df, "pivot_s1", pp.filter(like="S1").iloc[:,0] if not pp.empty else pd.Series(np.nan, index=df.index))
        _add(df, "pivot_r1", pp.filter(like="R1").iloc[:,0] if not pp.empty else pd.Series(np.nan, index=df.index))
    if patt.get("candle_patterns", False):
        # placeholder flags for patterns; actual candlestick detection can be extensive
        df["bullish_engulfing"] = ((df["close"] > df["open"]) & (df["open"].shift(1) > df["close"].shift(1))).astype(int)
        df["bearish_engulfing"] = ((df["close"] < df["open"]) & (df["open"].shift(1) < df["close"].shift(1))).astype(int)

    # --- Stats / ML ---
    sml = cfg.get("stats_ml", {})
    for n in sml.get("rolling_stats", []):
        df[f"roll_mean_{n}"] = close.rolling(n).mean()
        df[f"roll_std_{n}"]  = close.rolling(n).std()
        df[f"roll_skew_{n}"] = close.rolling(n).apply(lambda x: pd.Series(x).skew(), raw=False)
        df[f"roll_kurt_{n}"] = close.rolling(n).apply(lambda x: pd.Series(x).kurt(), raw=False)
    for n in sml.get("zscore", []):
        m = close.rolling(n).mean()
        s = close.rolling(n).std() + 1e-9
        df[f"zscore_{n}"] = (close - m) / s
    for l in sml.get("autocorr_lags", []):
        df[f"autocorr_{l}"] = close.pct_change().rolling(100).apply(lambda x: pd.Series(x).autocorr(lag=l))
    if sml.get("returns", False):
        df["ret_1"] = close.pct_change()
        df["logret_1"] = np.log(close).diff()
    for n in sml.get("percentile_range", []):
        roll_min = close.rolling(n).min()
        roll_max = close.rolling(n).max()
        df[f"pct_in_range_{n}"] = (close - roll_min) / (roll_max - roll_min + 1e-9)

    # HMM placeholder: computed externally in modeling stage if enabled
    return df
