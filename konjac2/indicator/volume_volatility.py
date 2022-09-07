import pandas as pd


def vol_volatility(close_price: pd.Series, span=100):
    df0 = close_price.index.searchsorted(close_price.index - pd.Timedelta(hours=1))
    df0 = df0[df0 > 0]
    df0 = pd.Series(close_price.index[df0 - 1], index=close_price.index[close_price.shape[0] - df0.shape[0]:])
    df0 = close_price.loc[df0.index] / close_price.loc[df0.values].values - 1
    df0 = df0.ewm(span=span).std()
    return df0
