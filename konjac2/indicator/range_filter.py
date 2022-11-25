from pandas import Series
from pandas_ta import ema


def range_filter(close: Series, length=100, multi=3.0):
    period = length * 2 - 1
    prev_close = close.shift(1)
    average_range = ema(abs(close - prev_close), length=length)
    smooth_range = ema(average_range, length=period) * multi
    rng_filter = []
    """
    rngfilt := x > nz(rngfilt[1]) ? x - r < nz(rngfilt[1]) ? nz(rngfilt[1]) : x - r : 
       x + r > nz(rngfilt[1]) ? nz(rngfilt[1]) : x + r
    """
    for price, prev_price, sr in zip(close, prev_close, smooth_range):
        if price > prev_price:
            if price - sr < prev_price:
                rng_filter.append(prev_price)
            else:
                rng_filter.append(price - sr)
        else:
            if price + sr > prev_price:
                rng_filter.append(prev_price)
            else:
                rng_filter.append(price + sr)

    upper = [0]
    lower = [0]
    for i, f in enumerate(rng_filter):
        pf = rng_filter[i - 1]
        if f > pf:
            upper.append(1)
        if f < pf:
            upper.append(0)
        else:
            upper.append(upper[-1])

        if f < pf:
            lower.append(1)
        if f > pf:
            lower.append(0)
        else:
            lower.append(lower[-1])

    return rng_filter, upper, lower
