# src/indicators/pta_shim.py
import pandas as pd
from ta.trend import EMAIndicator, SMAIndicator, WMAIndicator, ADXIndicator, CCIIndicator, PSARIndicator, MACD, AroonIndicator
from ta.momentum import RSIIndicator, StochasticOscillator, ROCIndicator, WilliamsRIndicator, StochRSIIndicator, TSIIndicator, AwesomeOscillatorIndicator
from ta.volatility import BollingerBands, KeltnerChannel, AverageTrueRange, DonchianChannel
from ta.volume import OnBalanceVolumeIndicator, ChaikinMoneyFlowIndicator, AccDistIndexIndicator, MFIIndicator, EaseOfMovementIndicator, VolumePriceTrendIndicator


class PandasTAShim:
    """
    Shim mínimo que expone métodos con nombres similares a pandas_ta.*
    Devuelve Series con nombre consistente.
    Agregá acá sólo lo que uses en tu proyecto.
    """

    @staticmethod
    def rsi(close: pd.Series, length: int = 14) -> pd.Series:
        s = RSIIndicator(close=close, window=length).rsi()
        return s.rename(f"RSI_{length}")

    @staticmethod
    def ema(close: pd.Series, length: int = 20) -> pd.Series:
        s = EMAIndicator(close=close, window=length).ema_indicator()
        return s.rename(f"EMA_{length}")

    @staticmethod
    def sma(close: pd.Series, length: int = 20) -> pd.Series:
        s = SMAIndicator(close=close, window=length).sma_indicator()
        return s.rename(f"SMA_{length}")

    @staticmethod
    def wma(close: pd.Series, length: int = 20) -> pd.Series:
        s = WMAIndicator(close=close, window=length).wma()
        return s.rename(f"WMA_{length}")

    @staticmethod
    def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
        macd = MACD(close=close, window_slow=slow,
                    window_fast=fast, window_sign=signal)
        return (
            macd.macd().rename(f"MACD_{fast}_{slow}"),
            macd.macd_signal().rename(f"MACDs_{signal}"),
            macd.macd_diff().rename("MACDh")
        )

    @staticmethod
    def adx(high: pd.Series, low: pd.Series, close: pd.Series, length: int = 14):
        adx = ADXIndicator(high=high, low=low, close=close, window=length)
        return (
            adx.adx().rename(f"ADX_{length}"),
            adx.adx_pos().rename(f"+DI_{length}"),
            adx.adx_neg().rename(f"-DI_{length}")
        )

    @staticmethod
    def cci(high: pd.Series, low: pd.Series, close: pd.Series, length: int = 20) -> pd.Series:
        return CCIIndicator(high=high, low=low, close=close, window=length).cci().rename(f"CCI_{length}")

    @staticmethod
    def stoch(high: pd.Series, low: pd.Series, close: pd.Series, length: int = 14):
        so = StochasticOscillator(
            high=high, low=low, close=close, window=length, smooth_window=3)
        return so.stoch().rename(f"STOCH_%K_{length}"), so.stoch_signal().rename(f"STOCH_%D_{length}")

    @staticmethod
    def stochrsi(close: pd.Series, length: int = 14):
        s = StochRSIIndicator(close=close, window=length, smooth1=3, smooth2=3)
        return s.stochrsi().rename(f"STOCHRSI_{length}")

    @staticmethod
    def roc(close: pd.Series, length: int = 10) -> pd.Series:
        return ROCIndicator(close=close, window=length).roc().rename(f"ROC_{length}")

    @staticmethod
    def willr(high: pd.Series, low: pd.Series, close: pd.Series, length: int = 14) -> pd.Series:
        return WilliamsRIndicator(high=high, low=low, close=close, lbp=length).williams_r().rename(f"WILLR_{length}")

    @staticmethod
    def tsi(close: pd.Series, long: int = 25, short: int = 13, signal: int = 7) -> pd.Series:
        return TSIIndicator(close=close, window_slow=long, window_fast=short).tsi().rename(f"TSI_{short}_{long}")

    @staticmethod
    def bbands(close: pd.Series, length: int = 20, ndev: float = 2.0):
        bb = BollingerBands(close=close, window=length, window_dev=ndev)
        return bb.bollinger_hband(), bb.bollinger_mavg(), bb.bollinger_lband(), bb.bollinger_hband_indicator()

    @staticmethod
    def keltner(high: pd.Series, low: pd.Series, close: pd.Series, length: int = 20, mult: float = 2.0):
        kc = KeltnerChannel(high=high, low=low, close=close,
                            window=length, original_version=False)
        return kc.keltner_channel_hband(), kc.keltner_channel_mband(), kc.keltner_channel_lband()

    @staticmethod
    def atr(high: pd.Series, low: pd.Series, close: pd.Series, length: int = 14) -> pd.Series:
        return AverageTrueRange(high=high, low=low, close=close, window=length).average_true_range().rename(f"ATR_{length}")

    @staticmethod
    def donchian(high: pd.Series, low: pd.Series, length: int = 20):
        dc = DonchianChannel(high=high, low=low, window=length)
        return dc.donchian_channel_hband(), dc.donchian_channel_lband(), dc.donchian_channel_wband()

    @staticmethod
    def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
        return OnBalanceVolumeIndicator(close=close, volume=volume).on_balance_volume().rename("OBV")

    @staticmethod
    def cmf(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, length: int = 20) -> pd.Series:
        return ChaikinMoneyFlowIndicator(high=high, low=low, close=close, volume=volume, window=length).chaikin_money_flow().rename(f"CMF_{length}")

    @staticmethod
    def adl(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
        return AccDistIndexIndicator(high=high, low=low, close=close, volume=volume).acc_dist_index().rename("ADL")

    @staticmethod
    def mfi(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, length: int = 14) -> pd.Series:
        return MFIIndicator(high=high, low=low, close=close, volume=volume, window=length).money_flow_index().rename(f"MFI_{length}")

    @staticmethod
    def eom(high: pd.Series, low: pd.Series, volume: pd.Series, length: int = 14) -> pd.Series:
        return EaseOfMovementIndicator(high=high, low=low, volume=volume, window=length).ease_of_movement().rename(f"EOM_{length}")

    @staticmethod
    def vpt(close: pd.Series, volume: pd.Series) -> pd.Series:
        return VolumePriceTrendIndicator(close=close, volume=volume).volume_price_trend().rename("VPT")
