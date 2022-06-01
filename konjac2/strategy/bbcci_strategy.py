from pandas_ta.momentum import cci

from .abc_strategy import ABCStrategy
from ..indicator.utils import TradeType, is_crossing_up, is_crossing_down
from ..indicator.bb_cci_momentum import bb_cci_mom
from ..bot.telegram_bot import say_something


class BBCCIStrategy(ABCStrategy):
    strategy_name = "bbcci"

    def __init__(self, symbol: str):
        ABCStrategy.__init__(self, symbol)

    def seek_trend(self, candles):
        trends, cci144 = bb_cci_mom(candlestick=candles)
        trend = None
        if is_crossing_up(cci144[-1], 80):
            trend = TradeType.long.name
        if is_crossing_down(cci144[-1], -80):
            trend = TradeType.short.name
        if trend is not None and trends[-3] and trends[-2] and trends[-1]:
            self._delete_last_in_progress_trade()
            self._start_new_trade(trend, candles.index[-1])

    def entry_signal(self, candles):
        cci34 = cci(candles.high, candles.low, candles.close, 34)
        last_order_status = self._can_open_new_trade()
        if last_order_status.ready_to_procceed and last_order_status.is_long and is_crossing_down(cci34[-1], -240):
            self._update_open_trade(TradeType.long.name, candles.close[-1], "cci34_240", cci34[-1], candles.index[-1])
            # say_something(f"{self.symbol} open {TradeType.long.name}")

        if last_order_status.ready_to_procceed and last_order_status.is_short and is_crossing_up(cci34[-1], 240):
            self._update_open_trade(TradeType.short.name, candles.close[-1], "cci34_240", cci34[-1], candles.index[-1])
            # say_something(f"{self.symbol} open {TradeType.short.name}")

    def exit_signal(self, candles):
        cci34 = cci(candles.high, candles.low, candles.close, 34)
        last_order_status = self._can_close_trade()
        if last_order_status.ready_to_procceed and last_order_status.is_long and cci34[-1] >= 160:
            is_profit, take_profit = self._is_take_profit(candles)
            is_loss, stop_loss = self._is_stop_loss(candles)
            self._update_close_trade(
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
            # say_something(f"{self.symbol} close {TradeType.long.name}")

        if last_order_status.ready_to_procceed and last_order_status.is_short and cci34[-1] <= -160:
            is_profit, take_profit = self._is_take_profit(candles)
            is_loss, stop_loss = self._is_stop_loss(candles)
            self._update_close_trade(
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
            # say_something(f"{self.symbol} close {TradeType.short.name}")
