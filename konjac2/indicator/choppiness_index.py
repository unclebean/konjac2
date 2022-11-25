import numpy as np
from pandas_ta import atr


def choppiness_index(candles, length=14):
    atr_ = atr(candles.high, candles.low, candles.close, length=length)
    high = candles.high.rolling(length).max()
    low = candles.low.rolling(length).min()
    ci = 100 * np.log10((atr_.rolling(length).sum()) / (high - low)) / np.log10(length)
    return ci