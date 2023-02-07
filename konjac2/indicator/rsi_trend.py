from pandas_ta import rsi, ema

from konjac2.indicator.utils import resample_to_interval


def rsi_trend(candles):
    # rsi_data = rsi(candles.close, length=14)
    # ema_data = ema(rsi_data, length=14)

    h3_candles = resample_to_interval(candles, interval=180)

    h3_rsi_data = rsi(h3_candles.close, length=14)
    h3_ema_data = ema(h3_rsi_data, length=14)

    return h3_rsi_data.values - h3_ema_data.values

