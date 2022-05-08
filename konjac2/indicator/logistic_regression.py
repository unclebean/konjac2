import numpy as np
import pandas as pd
from pandas_ta.overlap import ema, ichimoku
from pandas_ta.volatility import bbands
from pandas_ta.momentum import macd, cci, rsi
from sklearn.linear_model import LogisticRegression

from .vwap import VWAP

period = 34
period21 = 21
period13 = 13


def LogisticRegressionModel(candles):
    split = int(0.8 * len(candles))
    candles["S_10"] = candles["close"].rolling(window=21).mean()
    candles["Corr"] = candles["close"].rolling(window=21).corr(candles["S_10"])
    # candles["Open-Close"] = candles["open"] - candles["close"].shift(1)
    # candles["Open-Open"] = candles["open"] - candles["open"].shift(1)
    ichimoku_df, _ = ichimoku(candles.high, candles.low, candles.close)
    candles["t-k"] = ichimoku_df["ITS_9"] - ichimoku_df["IKS_26"]
    candles["s-s"] = ichimoku_df["ISA_9"] - ichimoku_df["ISB_26"]
    candles["macd"] = macd_to_series(candles.close)
    candles["bbands"] = bbands_to_series(candles.close, 21)
    candles["cci"] = cci_to_series(candles.high, candles.low, candles.close, 21)
    candles["rsi"] = rsi_to_series(candles.close, 21)
    candles["vwap"] = vwap_to_series(candles, 0)
    candles["efi"] = efi_to_series(candles.close, candles.volume, 13)
    candles["ema"] = ema_to_serires(candles.close)

    candles = candles.dropna()
    X = candles.iloc[0:-1, :16]
    y = np.where(candles["close"].shift(-1) > candles["close"], 1, -1)[1:]
    X_train, X_test, y_train, y_test = X[:split], X[split:], y[:split], y[split:]
    model = LogisticRegression()
    model = model.fit(X_train, y_train)
    return model.predict(candles.iloc[-1:, :16]), model.score(X_test, y_test)


def macd_to_series(close):
    macd_df = macd(close)
    values = []
    for (m, s, h) in zip(macd_df["MACD_12_26_9"], macd_df["MACDs_12_26_9"], macd_df["MACDh_12_26_9"]):
        values.append(m - s)
    return values


def bbands_to_series(close, period):
    bb_df = bbands(close, timeperiod=period)
    values = []
    for i, (u, m, l) in enumerate(zip(bb_df["BBU_5_2.0"], bb_df["BBM_5_2.0"], bb_df["BBL_5_2.0"])):
        if close[i] > m:
            values.append((u - close[i]))
        elif close[i] < m:
            values.append((l - close[i]))
        else:
            values.append(0)
    return pd.Series(values, bb_df["BBU_5_2.0"].index)


def cci_to_series(high, low, close, period):
    cci_series = cci(high, low, close, timeperiod=period)
    return cci_series.values


def rsi_to_series(close, period):
    rsi_series = rsi(close, timeperiod=period)
    return rsi_series.values


def vwap_to_series(candlesticks, delta_hours):
    close = candlesticks.close
    vwap, upper_band, lower_band = VWAP(candlestick=candlesticks, delta_hours=delta_hours, group_by="day")
    values = []
    for i, (u, v, l) in enumerate(zip(upper_band, vwap, lower_band)):
        if close[i] > v:
            values.append((u - close[i]))
        elif close[i] < v:
            values.append((l - close[i]))
        else:
            values.append(0)

    return pd.Series(values, upper_band.index)


def efi_to_series(close, volume, period):
    close_times_volume = close.diff(1) * volume
    efi = close_times_volume.ewm(ignore_na=False, span=period).mean()
    return efi


def ema_to_serires(close):
    fast = ema(close, 20).values
    slow = ema(close, 50).values
    return fast - slow
