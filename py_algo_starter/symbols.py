# -*- coding: utf-8 -*-
from __future__ import annotations

CRYPTO_BASES = {"BTC", "ETH"}
CRYPTO_SEPS = ("USDT", "USD", "BUSD")


def is_crypto_symbol(raw: str) -> bool:
    s = raw.strip().upper()
    # Casos típicos cripto: BTC, ETH, BTC/USDT, BTCUSDT, ETH-USD
    if "/" in s:
        left, right = s.split("/", 1)
        return left in CRYPTO_BASES or right in CRYPTO_SEPS
    if "-" in s:
        left, right = s.split("-", 1)
        return left in CRYPTO_BASES and right in CRYPTO_SEPS
    if s in CRYPTO_BASES:
        return True
    for q in CRYPTO_SEPS:
        if s.endswith(q) and s[:-len(q)] in CRYPTO_BASES:
            return True
    return False


def normalize_for_yahoo(raw: str) -> str:
    """
    Yahoo Finance:
    - Acciones/ETFs: AAPL, SPY
    - Cripto: BTC-USD, ETH-USD
    """
    s = raw.strip().upper()
    if is_crypto_symbol(s):
        if "/" in s:
            left, _ = s.split("/", 1)
            s = left
        for q in ("USDT", "BUSD"):
            if s.endswith(q):
                s = s[:-len(q)]
        if not s.endswith("-USD"):
            s = f"{s}-USD"
        return s
    # Equity/ETF: dejar tal cual (sin -USD)
    # Quitar separadores si alguien pasó AAPL/USD, AAPLUSDT, etc.
    s = s.replace("/", "").replace("USDT",
                                   "").replace("USD", "").replace("BUSD", "")
    return s


def normalize_for_exchange(raw: str) -> str:
    """
    Para exchange cripto (si en el futuro usás CCXT): BTC/USDT, ETH/USDT
    """
    s = raw.strip().upper()
    if is_crypto_symbol(s):
        base = s
        # Reconstruir como BASE/USDT por defecto
        for q in ("-USD", "-USDT"):
            base = base.replace(q, "")
        for q in ("USDT", "USD", "BUSD"):
            base = base.replace(q, "")
        return f"{base}/USDT"
    return s
