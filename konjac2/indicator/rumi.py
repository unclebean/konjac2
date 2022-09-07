from pandas_ta import sma, ema
from pandas import Series


def rumi_v1(close: Series):
    short_ema = ema(close, 18)
    long_ema = ema(close, 110)
    diff = short_ema - long_ema
    return ema(diff, 31)


def rumi_v2(close: Series):
    short_ma = sma(close, 3)
    long_ema = ema(close, 100)
    diff = short_ma - long_ema
    return sma(diff, 30)
