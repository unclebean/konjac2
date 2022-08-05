import logging

from pandas_ta import ema
from pandas_ta.momentum import cci

from .abc_strategy import ABCStrategy
from ..indicator.utils import TradeType, is_crossing_up, is_crossing_down

log = logging.getLogger(__name__)


class CCIEMaStrategy(ABCStrategy):
    strategy_name = "cci_ema"

    def __init__(self, symbol: str):
        ABCStrategy.__init__(self, symbol)

    def seek_trend(self, candles, day_candles=None):
        cci25 = cci(candles.high, candles.low, candles.close, 25)
        cci50 = cci(candles.high, candles.low, candles.close, 50)
        trend = None
        if is_crossing_up(cci25[-1], 0) and is_crossing_up(cci50[-1], 0):
            trend = TradeType.long.name
        if is_crossing_down(cci25[-1], 0) and is_crossing_down(cci50[-1], 0):
            trend = TradeType.short.name
        if trend is not None:
            self._delete_last_in_progress_trade()
            self._start_new_trade(trend, candles.index[-1])

    def entry_signal(self, candles, day_candles=None):
        prev_close_price = candles.close[-2]
        close_price = candles.close[-1]
        ema_34 = ema(candles.close, 34)
        last_order_status = self._can_open_new_trade()
        if last_order_status.ready_to_procceed \
                and last_order_status.is_long \
                and ema_34[-1] < close_price \
                and prev_close_price <= ema_34[-2]:
            return self._update_open_trade(TradeType.long.name, candles.close[-1], "ema_34", ema_34[-1], candles.index[-1])
            # say_something(f"{self.symbol} open {TradeType.long.name}")

        if last_order_status.ready_to_procceed \
                and last_order_status.is_short \
                and ema_34[-1] > close_price \
                and prev_close_price >= ema_34[-2]:
            return self._update_open_trade(TradeType.short.name, candles.close[-1], "ema_34", ema_34[-1], candles.index[-1])
            # say_something(f"{self.symbol} open {TradeType.short.name}")

    def exit_signal(self, candles, day_candles=None):
        close_price = candles.close[-1]
        ema_34 = ema(candles.close, 34)
        last_order_status = self._can_close_trade()
        is_profit, take_profit = self._is_take_profit(candles)
        is_loss, stop_loss = self._is_stop_loss(candles)
        if last_order_status.ready_to_procceed and last_order_status.is_long \
                and (ema_34[-1] >= close_price or is_loss or is_profit):
            return self._update_close_trade(
                TradeType.short.name,
                candles.close[-1],
                "ema_34",
                ema_34[-1],
                candles.index[-1],
                is_profit,
                is_loss,
                take_profit,
                stop_loss,
            )

        if last_order_status.ready_to_procceed and last_order_status.is_short \
                and (ema_34[-1] <= close_price or is_loss or is_profit):
            return self._update_close_trade(
                TradeType.long.name,
                candles.close[-1],
                "ema_34",
                ema_34[-1],
                candles.index[-1],
                is_profit,
                is_loss,
                take_profit,
                stop_loss,
            )
