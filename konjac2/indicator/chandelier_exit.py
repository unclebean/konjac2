from pandas_ta.volatility import atr


def chandelier_exit(candlestick, period=22):
    atr_value = atr(candlestick.high, candlestick.low, candlestick.close, period) * 3
    long_exit = candlestick.close.rolling(period).max() - atr_value
    short_exit = candlestick.close.rolling(period).max() + atr_value
    indicators = []
    for long_stop, short_stop, close_price in zip(long_exit, short_exit, candlestick.close):
        if close_price > short_stop:
            indicators.append(1)
        elif close_price < long_stop:
            indicators.append(-1)
        else:
            indicators.append(1)

    return indicators


def chandelier_trend(long_exit, short_exit, close):
    long_stop_prev = long_exit[-2]
    long_stop = max(long_exit[-1], long_stop_prev) if close[-2] > long_stop_prev else long_exit[-1]

    short_stop_prev = short_exit[-2]
    short_stop = min(short_exit[-1], short_stop_prev) if close[-2] < short_stop_prev else short_exit[-1]

    dir = 1
    if close[-1] > short_stop_prev:
        dir = 1
    elif close[-1] < long_stop_prev:
        dir = -1

    return dir