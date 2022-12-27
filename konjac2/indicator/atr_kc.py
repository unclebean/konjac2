from pandas_ta import ema, atr


def atr_kc(candles):
    ema_ = ema(candles.close, length=20)
    atr_ = atr(candles.high, candles.low, candles.close, length=10)
    kc_upper = ema_ + atr_ * 1.5
    kc_lower = ema_ - atr_ * 1.5

    return kc_upper, kc_lower