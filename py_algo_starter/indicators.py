# -*- coding: utf-8 -*-
from __future__ import annotations
import pandas as pd
import numpy as np


def ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False, min_periods=span).mean()


def rsi(series: pd.Series, length: int = 14) -> pd.Series:
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    roll_up = up.ewm(alpha=1/length, adjust=False).mean()
    roll_down = down.ewm(alpha=1/length, adjust=False).mean()
    rs = roll_up / (roll_down.replace(0, np.nan))
    out = 100 - (100 / (1 + rs))
    return out.fillna(50)


def atr(df: pd.DataFrame, length: int = 14) -> pd.Series:
    high, low, close = df["high"], df["low"], df["close"]
    prev_close = close.shift(1)
    tr = pd.concat([
        (high - low),
        (high - prev_close).abs(),
        (low - prev_close).abs()
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1/length, adjust=False, min_periods=length).mean()


def pivots_classic(df: pd.DataFrame) -> pd.DataFrame:
    # Usar último día para pivots diarios
    daily = df.resample("1D").agg(
        {"high": "max", "low": "min", "close": "last"}).dropna()
    p = (daily["high"] + daily["low"] + daily["close"]) / 3.0
    r1 = 2*p - daily["low"]
    s1 = 2*p - daily["high"]
    r2 = p + (daily["high"] - daily["low"])
    s2 = p - (daily["high"] - daily["low"])
    piv = pd.DataFrame({"P": p, "R1": r1, "S1": s1, "R2": r2, "S2": s2})
    # ffill a intradía
    piv_i = piv.reindex(df.index, method="ffill")
    return piv_i


def compute_signals(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["EMA20"] = ema(out["close"], 20)
    out["EMA50"] = ema(out["close"], 50)
    out["RSI14"] = rsi(out["close"], 14)
    out["ATR14"] = atr(out, 14)
    piv = pivots_classic(out)
    out = out.join(piv)

    # Señales base
    # Buy: EMA20>EMA50 + RSI>50 + close rompe R1 (breakout) => entrada = R1 + 0.2*ATR
    # Sell: close < EMA20 o RSI<45 o take-profit cerca de R2 => salida = max(S1 - 0.2*ATR, EMA50)
    cond_buy = (out["EMA20"] > out["EMA50"]) & (
        out["RSI14"] > 50) & (out["close"] > out["R1"])
    cond_tp = out["close"] >= out["R2"]  # target alcanzado

    # salida por stop/condiciones
    cond_stop = (out["close"] < out["EMA20"]) | (out["RSI14"] < 45)

    out["ENTRY_PRICE"] = (out["R1"] + 0.2*out["ATR14"]).where(cond_buy)
    raw_stop = (out["S1"] - 0.2*out["ATR14"]).where(cond_buy)
    out["STOP_LOSS"] = np.maximum(
        raw_stop.fillna(-np.inf), (out["EMA50"]).fillna(-np.inf)).where(cond_buy)

    # Salida sugerida
    out["EXIT_PRICE"] = np.select(
        [
            cond_tp,
            cond_stop
        ],
        [
            np.maximum(out["R2"] - 0.2*out["ATR14"],
                       out["close"]),  # TP dinámico
            out["EMA50"]  # salida conservadora
        ],
        default=np.nan
    )

    # Semáforo
    # 🟢 si cond_buy y precio < R2
    # 🟡 si lateral: EMA20~EMA50 (±0.5%) o RSI entre 45-55
    # 🔴 si cond_stop
    ema_rel = (out["EMA20"] - out["EMA50"]) / out["EMA50"].replace(0, np.nan)
    lateral = (ema_rel.abs() <= 0.005) | (
        (out["RSI14"] >= 45) & (out["RSI14"] <= 55))
    semaforo = np.where(cond_stop, "🔴",
                        np.where(cond_buy & (out["close"] < out["R2"]), "🟢",
                                 np.where(lateral, "🟡", "🟡")))
    out["TRAFFIC"] = semaforo

    # Texto de conclusión (breve)
    conclusion = []
    for i, row in out.iterrows():
        msg = None
        if row["TRAFFIC"] == "🟢" and not np.isnan(row.get("ENTRY_PRICE", np.nan)):
            msg = f"Posible entrada sobre {row['ENTRY_PRICE']:.2f}; stop {row['STOP_LOSS']:.2f}; TP {max(row['R2']-0.2*row['ATR14'], row['close']):.2f}"
        elif row["TRAFFIC"] == "🔴":
            msg = f"Salir bajo EMA20 o RSI<45; referencia {row['EMA50']:.2f}"
        else:
            msg = "Esperar confirmación (EMA20≈EMA50 o RSI 45–55)"
        conclusion.append(msg)
    out["CONCLUSION"] = conclusion

    return out
