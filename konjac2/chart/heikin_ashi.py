import pandas as pd
from pandas_ta import sma, ema


def heikin_ashi(df):
    heikin_ashi_df = pd.DataFrame(index=df.index.values, columns=["open", "high", "low", "close", "volume"])

    heikin_ashi_df["close"] = (df["open"] + df["high"] + df["low"] + df["close"]) / 4

    for i in range(len(df)):
        if i == 0:
            heikin_ashi_df.iat[0, 0] = df["open"].iloc[0]
        else:
            heikin_ashi_df.iat[i, 0] = (heikin_ashi_df.iat[i - 1, 0] + heikin_ashi_df.iat[i - 1, 3]) / 2

    heikin_ashi_df["high"] = heikin_ashi_df.loc[:, ["open", "close"]].join(df["high"]).max(axis=1)

    heikin_ashi_df["low"] = heikin_ashi_df.loc[:, ["open", "close"]].join(df["low"]).min(axis=1)

    heikin_ashi_df["volume"] = df["volume"]
    heikin_ashi_df.index.name = "date"

    return heikin_ashi_df


def sma_heikin_ashi(df, length=40, smoothed_length=40):
    open_sma = sma(df.open, length)
    high_sma = sma(df.high, length)
    low_sma = sma(df.low, length)
    close_sma = sma(df.close, length)
    heikin_ashi_df = pd.DataFrame(index=df.index.values, columns=["open", "high", "low", "close", "volume"])

    heikin_ashi_df["close"] = (open_sma + high_sma + low_sma + close_sma) / 4

    for i in range(len(df)):
        if i == 0:
            heikin_ashi_df.iat[0, 0] = (open_sma[0] + close_sma[0]) / 2
        else:
            heikin_ashi_df.iat[i, 0] = (open_sma[i-1] + close_sma[i-1]) / 2

    heikin_ashi_df["high"] = heikin_ashi_df.loc[:, ["open", "close"]].join(high_sma).max(axis=1)

    heikin_ashi_df["low"] = heikin_ashi_df.loc[:, ["open", "close"]].join(low_sma).min(axis=1)

    # cha = ema(heikin_ashi_df.close, smoothed_length)
    # oha = ema(heikin_ashi_df.open, smoothed_length)
    # hha = ema(heikin_ashi_df.high, smoothed_length)
    # lha = ema(heikin_ashi_df.low, smoothed_length)

    cha = heikin_ashi_df.close
    oha = heikin_ashi_df.open
    hha = heikin_ashi_df.high
    lha = heikin_ashi_df.low

    return cha, oha, hha, lha
