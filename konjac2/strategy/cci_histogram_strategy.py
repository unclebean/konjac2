import logging

from pandas_ta.momentum import cci

from .abc_strategy import ABCStrategy
from ..indicator.squeeze_momentum import is_squeeze
from ..indicator.utils import TradeType

log = logging.getLogger(__name__)


class CCIHistogramStrategy(ABCStrategy):
    strategy_name = "cci histogram"

    def __init__(self, symbol: str):
        ABCStrategy.__init__(self, symbol)

    def seek_trend(self, candles, day_candles=None):
        is_sqz = is_squeeze(candles)
        if not is_sqz:
            self._delete_last_in_progress_trade()
            self._start_new_trade(TradeType.long.name, candles.index[-1])

    def entry_signal(self, candles, day_candles=None):
        cci34 = cci(candles.high, candles.low, candles.close, 34)
        cci144 = cci(candles.high, candles.low, candles.close, 144)
        last_order_status = self._can_open_new_trade()
        if last_order_status.ready_to_procceed and cci34[-1] > cci144[-1] and cci34[-2] <= cci144[-2]:
            return self._update_open_trade(TradeType.long.name, candles.close[-1], "cci34_144", cci34[-1], candles.index[-1])

        if last_order_status.ready_to_procceed and cci34[-1] < cci144[-1] and cci34[-2] >= cci144[-2]:
            return self._update_open_trade(TradeType.short.name, candles.close[-1], "cci34_144", cci34[-1], candles.index[-1])

    def exit_signal(self, candles, day_candles=None):
        cci34 = cci(candles.high, candles.low, candles.close, 34)
        cci144 = cci(candles.high, candles.low, candles.close, 144)
        histogram = cci34 - cci144
        last_order_status = self._can_close_trade()
        is_profit, take_profit = self._is_take_profit(candles)
        is_loss, stop_loss = self._is_stop_loss(candles)
        if last_order_status.ready_to_procceed and last_order_status.is_long \
                and (histogram[-1] < histogram[-2] or is_loss or is_profit):
            return self._update_close_trade(
                TradeType.short.name,
                candles.close[-1],
                "cci34_240",
                cci34[-1],
                candles.index[-1],
                is_profit,
                is_loss,
                take_profit,
                stop_loss,
            )

        if last_order_status.ready_to_procceed and last_order_status.is_short \
                and (histogram[-1] > histogram[-2] or is_loss or is_profit):
            return self._update_close_trade(
                TradeType.long.name,
                candles.close[-1],
                "cci34_240",
                cci34[-1],
                candles.index[-1],
                is_profit,
                is_loss,
                take_profit,
                stop_loss,
            )
