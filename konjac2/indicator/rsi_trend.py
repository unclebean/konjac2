from pandas_ta import rsi, ema


def rsi_trend(candles):
    rsi_data = rsi(candles.close, length=14)
    ema_data = ema(rsi_data, length=14)

    h3_rsi_data = rsi_data.resample("180min", label="left").mean()
    h3_ema_data = ema_data.resample("180min", label="left").mean()

    return h3_rsi_data.values - h3_ema_data.values

