from pandas_ta import cci
from pandas_ta.momentum import rsi

from .abc_strategy import ABCStrategy
from ..chart.heikin_ashi import heikin_ashi
from ..indicator.chandelier_exit import chandelier_exit
from ..indicator.utils import TradeType


class CERSIStrategy(ABCStrategy):
    strategy_name = "ce rsi"

    def __init__(self, symbol: str):
        ABCStrategy.__init__(self, symbol)

    def seek_trend(self, candles, middle_candles=None, long_candles=None):
        heikin_ashi_candles = heikin_ashi(candles)
        signals = chandelier_exit(heikin_ashi_candles)

        if signals[-1] == 1 and signals[-2] == -1:
            self._delete_last_in_progress_trade()
            self._start_new_trade(TradeType.long.name, candles.index[-1])
        if signals[-1] == -1 and signals[-2] == 1:
            self._delete_last_in_progress_trade()
            self._start_new_trade(TradeType.short.name, candles.index[-1])

    def entry_signal(self, candles, middle_candles=None, long_candles=None):
        cci34 = cci(candles.high, candles.low, candles.close, 34)
        cci144 = cci(candles.high, candles.low, candles.close, 144)
        last_order_status = self._can_open_new_trade()
        if last_order_status.ready_to_procceed \
                and last_order_status.is_long \
                and cci34[-1] > cci144[-1]\
                and cci34[-2] < cci144[-2]:
            self._update_open_trade(TradeType.long.name, candles.close[-1], "ce_rsi", cci34[-1],
                                    candles.index[-1])

        if last_order_status.ready_to_procceed \
                and last_order_status.is_short \
                and cci34[-1] < cci144[-1]\
                and cci34[-2] > cci144[-2]:
            self._update_open_trade(TradeType.short.name, candles.close[-1], "ce_rsi", cci34[-1],
                                    candles.index[-1])
            # say_something(f"{self.symbol} open {TradeType.short.name}")

    def exit_signal(self, candles, middle_candles=None, long_candles=None):
        heikin_ashi_candles = heikin_ashi(candles)
        signals = chandelier_exit(heikin_ashi_candles)
        cci34 = cci(candles.high, candles.low, candles.close, 34)
        cci144 = cci(candles.high, candles.low, candles.close, 144)
        last_order_status = self._can_close_trade()
        is_profit, take_profit = self._is_take_profit(candles)
        is_loss, stop_loss = self._is_stop_loss(candles)
        if last_order_status.ready_to_procceed and last_order_status.is_long and (
                signals[-1] == -1 or cci34[-1] < cci144[-1] or is_loss or is_profit):
            self._update_close_trade(
                TradeType.short.name,
                candles.close[-1],
                "ce_rsi",
                signals[-1],
                candles.index[-1],
                is_profit,
                is_loss,
                take_profit,
                stop_loss,
            )

        if last_order_status.ready_to_procceed and last_order_status.is_short and (
                signals[-1] == 1 or cci34[-1] > cci144[-1] or is_loss or is_profit):
            self._update_close_trade(
                TradeType.long.name,
                candles.close[-1],
                "ce_rsi",
                signals[-1],
                candles.index[-1],
                is_profit,
                is_loss,
                take_profit,
                stop_loss,
            )
