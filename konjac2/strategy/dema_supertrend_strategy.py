from pandas_ta.overlap import supertrend, dema
from .abc_strategy import ABCStrategy
from ..indicator.squeeze_momentum import is_squeeze
from ..indicator.utils import TradeType


class DemaSuperTrendStrategy(ABCStrategy):
    strategy_name = "dema_supertrend"

    def __init__(self, symbol: str):
        ABCStrategy.__init__(self, symbol)

    def seek_trend(self, candles, day_candles=None):
        dema144 = dema(candles.close, length=144)[-1]
        dema169 = dema(candles.close, length=169)[-1]
        close_price = candles.close[-1]
        trend = None
        if close_price > dema144 and close_price > dema169:
            trend = TradeType.long.name
        if close_price < dema144 and close_price < dema169:
            trend = TradeType.short.name
        if trend is not None:
            self._delete_last_in_progress_trade()
            self._start_new_trade(trend, candles.index[-1])

    def entry_signal(self, candles, day_candles=None):
        super_trend = supertrend(candles.high, candles.low, candles.close, length=34, multiplier=3)["SUPERT_34_3"]
        last_order_status = self._can_open_new_trade()
        is_in_squeeze = is_squeeze(candles)
        if (
            last_order_status.ready_to_procceed
            and last_order_status.is_long
            and not is_in_squeeze
        ):
            self._update_open_trade(
                TradeType.long.name, candles.close[-1], "super_trend", super_trend[-1], candles.index[-1]
            )
        if (
            last_order_status.ready_to_procceed
            and last_order_status.is_short
            and not is_in_squeeze
        ):
            self._update_open_trade(
                TradeType.short.name, candles.close[-1], "super_trend", super_trend[-1], candles.index[-1]
            )

    def exit_signal(self, candles, day_candles=None):
        super_trend = supertrend(candles.high, candles.low, candles.close, length=34, multiplier=3)['SUPERT_34_3']
        last_order_status = self._can_close_trade()
        is_in_squeeze = is_squeeze(candles)
        if (
            last_order_status.ready_to_procceed
            and last_order_status.is_long
            and is_in_squeeze
        ):
            self._update_close_trade(
                TradeType.short.name, candles.close[-1], "super_trend", super_trend[-1], candles.index[-1]
            )
        if (
            last_order_status.ready_to_procceed
            and last_order_status.is_short
            and is_in_squeeze
        ):
            self._update_close_trade(
                TradeType.long.name, candles.close[-1], "super_trend", super_trend[-1], candles.index[-1]
            )
