from collections import deque

from scipy.signal import argrelextrema
import numpy as np


def get_higher_highs(data: np.array, order=5, K=2):
    high_idx = argrelextrema(data, np.greater, order=order)[0]
    highs = data[high_idx]
    extrema = []
    ex_deque = deque(maxlen=K)
    for i, idx in enumerate(high_idx):
        if i == 0:
            ex_deque.append(idx)
            continue
        if highs[i] < highs[i - 1]:
            ex_deque.clear()

        ex_deque.append(idx)
        if len(ex_deque) == K:
            extrema.append(ex_deque.copy())

    if len(extrema) == 0:
        return [[-1, -1]]

    return extrema


def get_lower_lows(data: np.array, order=5, K=2):
    low_idx = argrelextrema(data, np.less, order=order)[0]
    lows = data[low_idx]
    # Ensure consecutive lows are lower than previous lows
    extrema = []
    ex_deque = deque(maxlen=K)
    for i, idx in enumerate(low_idx):
        if i == 0:
            ex_deque.append(idx)
            continue
        if lows[i] > lows[i - 1]:
            ex_deque.clear()

        ex_deque.append(idx)
        if len(ex_deque) == K:
            extrema.append(ex_deque.copy())

    if len(extrema) == 0:
        return [[-1, -1]]

    return extrema


def get_higher_lows(data: np.array, order=5, K=2):
    # Get lows
    low_idx = argrelextrema(data, np.less, order=order)[0]
    lows = data[low_idx]
    # Ensure consecutive lows are higher than previous lows
    extrema = []
    ex_deque = deque(maxlen=K)
    for i, idx in enumerate(low_idx):
        if i == 0:
            ex_deque.append(idx)
            continue
        if lows[i] < lows[i - 1]:
            ex_deque.clear()

        ex_deque.append(idx)
        if len(ex_deque) == K:
            extrema.append(ex_deque.copy())

    if len(extrema) == 0:
        return [[-1, -1]]

    return extrema


def get_lower_highs(data: np.array, order=5, K=2):
    # Get highs
    high_idx = argrelextrema(data, np.greater, order=order)[0]
    highs = data[high_idx]
    # Ensure consecutive highs are lower than previous highs
    extrema = []
    ex_deque = deque(maxlen=K)
    for i, idx in enumerate(high_idx):
        if i == 0:
            ex_deque.append(idx)
            continue
        if highs[i] > highs[i - 1]:
            ex_deque.clear()

        ex_deque.append(idx)
        if len(ex_deque) == K:
            extrema.append(ex_deque.copy())

    if len(extrema) == 0:
        return [[-1, -1]]

    return extrema


def is_long_or_short(candles):
    close_values = candles.close.values
    higher_high = get_higher_highs(close_values)[-1][1]
    lower_low = get_lower_lows(close_values)[-1][1]
    higher_low = get_higher_lows(close_values)[-1][1]
    lower_high = get_lower_highs(close_values)[-1][1]

    is_long = (higher_high > lower_low and higher_high > lower_high) \
              or (higher_low > lower_low and higher_low > lower_high)

    is_short = (lower_low > higher_high and lower_low > higher_low) \
               or (lower_high > higher_high and lower_high > higher_low)

    return is_long, is_short
