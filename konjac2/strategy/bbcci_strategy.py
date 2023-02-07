import logging

from pandas_ta.momentum import cci

from .abc_strategy import ABCStrategy
from ..indicator.utils import TradeType, is_crossing_up, is_crossing_down
from ..indicator.bb_cci_momentum import bb_cci_mom

log = logging.getLogger(__name__)


class BBCCIStrategy(ABCStrategy):
    strategy_name = "bbcci"

    def __init__(self, symbol: str, trade_short_order=True, trade_long_order=True):
        ABCStrategy.__init__(self, symbol)

    def seek_trend(self, candles, day_candles=None):
        trends, cci144 = bb_cci_mom(candlestick=candles)
        trend = None
        if is_crossing_up(cci144[-1], 80):
            trend = TradeType.long.name
        if is_crossing_down(cci144[-1], -80):
            trend = TradeType.short.name
        log.info(f"{self.symbol} BBCCI trend {trend} at {candles.index[-1]}")
        if trend is not None and trends[-4] and trends[-3] and trends[-2] and trends[-1]:
            self._delete_last_in_progress_trade()
            self._start_new_trade(trend, candles.index[-1])

    def entry_signal(self, candles, day_candles=None):
        cci144, cci34, diff_value = self._get_cci_diff(candles)
        last_order_status = self._can_open_new_trade()
        if last_order_status.ready_to_procceed and last_order_status.is_long and diff_value > 240 and cci144[-1] > 0:
            return self._update_open_trade(TradeType.long.name, candles.close[-1], "cci34_240", cci34[-1],
                                           candles.index[-1])
            # say_something(f"{self.symbol} open {TradeType.long.name}")

        if last_order_status.ready_to_procceed and last_order_status.is_short and diff_value > 240 and cci144[-1] < 0:
            return self._update_open_trade(TradeType.short.name, candles.close[-1], "cci34_240", cci34[-1],
                                           candles.index[-1])
            # say_something(f"{self.symbol} open {TradeType.short.name}")

    def exit_signal(self, candles, day_candles=None):
        cci144, cci34, diff_value = self._get_cci_diff(candles)
        last_order_status = self._can_close_trade()
        is_profit, take_profit = self._is_take_profit(candles)
        is_loss, stop_loss = self._is_stop_loss(candles)
        if last_order_status.ready_to_procceed and last_order_status.is_long \
                and (diff_value < 160 or is_loss or is_profit):
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
                and (diff_value < 160 or is_loss or is_profit):
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

    def _get_cci_diff(self, candles):
        cci34 = cci(candles.high, candles.low, candles.close, 34)
        cci144 = cci(candles.high, candles.low, candles.close, 144)
        diff_value = abs(cci34[-1] - cci144[-1])
        return cci144, cci34, diff_value
