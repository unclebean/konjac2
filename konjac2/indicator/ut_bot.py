import vectorbt as vbt
import pandas as pd
import numpy as np
from pandas_ta import atr

# UT Bot Parameters
SENSITIVITY = 2
ATR_PERIOD = 6


def xATRTrailingStop_func(close, prev_close, prev_atr, nloss):
    if close > prev_atr and prev_close > prev_atr:
        return max(prev_atr, close - nloss)
    elif close < prev_atr and prev_close < prev_atr:
        return min(prev_atr, close + nloss)
    elif close > prev_atr:
        return close - nloss
    else:
        return close + nloss


def ut_bot(candles):
    xATR = atr(candles.high, candles.low, candles.close, timeperiod=ATR_PERIOD)
    nLoss = SENSITIVITY * xATR
    pd_data = pd.DataFrame({"xATR": xATR, "nLoss": nLoss, "close": candles.close})
    pd_data = pd_data.dropna()
    pd_data = pd_data.reset_index()
    pd_data["ATRTrailingStop"] = [0.0] + [np.nan for i in range(len(pd_data) - 1)]

    for i in range(1, len(pd_data)):
        pd_data.loc[i, "ATRTrailingStop"] = xATRTrailingStop_func(
            pd_data["close"].iat[i],
            pd_data["close"].iat[i - 1],
            pd_data["ATRTrailingStop"].iat[i - 1],
            pd_data["nLoss"].iat[i],
        )

    ema = vbt.MA.run(pd_data["close"], 1, short_name='EMA', ewm=True)

    pd_data["Above"] = ema.ma_crossed_above(pd_data["ATRTrailingStop"])
    pd_data["Below"] = ema.ma_crossed_below(pd_data["ATRTrailingStop"])

    pd_data["Buy"] = (pd_data["close"] > pd_data["ATRTrailingStop"]) & (pd_data["Above"] == True)
    pd_data["Sell"] = (pd_data["close"] < pd_data["ATRTrailingStop"]) & (pd_data["Below"] == True)

    return pd_data