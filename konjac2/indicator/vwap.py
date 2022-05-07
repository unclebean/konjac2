from pandas_ta.momentum import rsi
import numpy as np
import pandas as pd


def VWAP(candlestick, delta_hours=2, group_by="day"):
    candlestick.index = candlestick.index + pd.Timedelta(hours=delta_hours)
    group_by_conditions = (
        [candlestick.index.year, candlestick.index.month, candlestick.index.day]
        if group_by == "day"
        else [candlestick.index.year, candlestick.index.isocalendar().week]
    )
    candlesGroupByDay = candlestick.groupby(by=group_by_conditions)
    vwaps = []
    upper_bands = []
    lower_bands = []
    for key, item in candlesGroupByDay:
        candles = candlesGroupByDay.get_group(key).sort_index()
        vwap = mr_right_vwap(candles.high, candles.low, candles.close, candles.volume, len(candles))
        stDev = np.std(vwap)
        upper_band = vwap + stDev * 2
        lower_band = vwap - stDev * 2
        vwaps.append(vwap)
        upper_bands.append(upper_band)
        lower_bands.append(lower_band)

    concatVwap = pd.concat(vwaps)
    concatVwap = concatVwap.sort_index()
    concatVwap.index = concatVwap.index - pd.Timedelta(hours=delta_hours)

    concatUpperBands = pd.concat(upper_bands)
    concatUpperBands = concatUpperBands.sort_index()
    concatUpperBands.index = concatUpperBands.index - pd.Timedelta(hours=delta_hours)

    concatLowerBands = pd.concat(lower_bands)
    concatLowerBands = concatLowerBands.sort_index()
    concatLowerBands.index = concatLowerBands.index - pd.Timedelta(hours=delta_hours)

    return concatVwap, concatUpperBands, concatLowerBands


def RSI_VWAP(candlestick, delta_hours=0, group_by="day"):
    '''
    vwap = VolumeWeightedAveragePrice(
        candlestick.high, candlestick.low, candlestick.close, candlestick.volume, window=14
    )
    rsi_series = talib.RSI(vwap.volume_weighted_average_price(), timeperiod=17)
    '''
    vwap_values, _, _ = VWAP(candlestick, delta_hours=0, group_by=group_by)
    rsi_series = rsi(vwap_values, timeperiod=17)
    return rsi_series


def mr_right_vwap(high, low, close, volume, count):
    tp = (high + low + close) / 3.0
    pv = tp * volume
    total_pv = pv.rolling(count, min_periods=1).sum()
    total_volume = volume.rolling(count, min_periods=1).sum()
    return total_pv / total_volume
