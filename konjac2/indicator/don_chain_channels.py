import pandas as pd


def don_chain_channels(candles: pd.DataFrame, period: int = 20):
    upper_don = candles.high.rolling(period).max()
    lower_don = candles.low.rolling(period).min()
    mid_don = (upper_don + lower_don) / 2
    return upper_don, mid_don, lower_don
