from numpy import short
from pandas_ta.volatility import atr


def chandelier_exit(candlestick, period=22):
    long_exit = (
        candlestick.high.rolling(period).max() - atr(candlestick.high, candlestick.low, candlestick.close, period) * 3
    )
    short_exit = (
        candlestick.low.rolling(period).max() + atr(candlestick.high, candlestick.low, candlestick.close, period) * 3
    )

    return long_exit, short_exit
