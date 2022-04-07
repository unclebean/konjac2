from pandas_ta.momentum import cci
from pandas_ta.volatility import bbands
from .utils import is_crossing_up, is_crossing_down


def bb_cci_mom(candlestick):
    bb_55 = bbands(candlestick.close, 55)
    cci_144 = cci(candlestick.high, candlestick.low, candlestick.close, 144)
    bb_55_low = bb_55["BBL_55_2.0"]
    bb_55_up = bb_55["BBU_55_2.0"]

    return (is_crossing_up(candlestick.close, bb_55_up) & is_crossing_up(cci_144, 80)) | (
        is_crossing_down(candlestick.close, bb_55_low) & is_crossing_down(cci_144, 80)
    ), cci_144


def cci_entry_exit_signal(candlestick):
    cci_144 = cci(candlestick.high, candlestick.low, candlestick.close, 144)
    cci_34 = cci(candlestick.high, candlestick.low, candlestick.close, 34)
    return is_crossing_up(cci_34, 240) | is_crossing_down(cci_34, -240), cci_34, cci_144
