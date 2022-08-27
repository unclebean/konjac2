from enum import Enum

from pandas import DatetimeIndex, DataFrame


class TradeType(Enum):
    long = 0
    short = 1


class SignalCondition(Enum):
    crossing_up = 0
    crossing_down = 1
    moving_up = 2
    moving_down = 3


def is_crossing_up(source, target):
    return source > target


def is_crossing_down(source, target):
    return source < target


def resample_to_interval(dataframe: DataFrame, interval=240):
    """
    Resamples the given dataframe to the desired interval.
    Please be aware you need to use resampled_merge to merge to another dataframe to
    avoid lookahead bias
    :param dataframe: dataframe containing close/high/low/open/volume
    :param interval: to which ticker value in minutes would you like to resample it
    :return:
    """

    df = dataframe.copy()
    ohlc_dict = {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
    # Resample to "left" border as dates are candle open dates
    df = df.resample(str(interval) + "min", label="left").agg(ohlc_dict).dropna()
    df.reset_index(inplace=True)
    df = df.set_index(DatetimeIndex(df["date"]))

    return df