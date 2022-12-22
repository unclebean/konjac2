import logging

from pandas_ta import ema

from .abc_strategy import ABCStrategy
from ..indicator.squeeze_momentum import is_squeeze
from ..indicator.utils import TradeType

log = logging.getLogger(__name__)


class EmaSqueezeStrategy(ABCStrategy):
    strategy_name = "ema squeeze"

    def __init__(self, symbol: str, trade_short_order=True):
        ABCStrategy.__init__(self, symbol, trade_short_order)

    def seek_trend(self, candles, day_candles=None):
        ema_10 = ema(candles.close, 10)
        ema_20 = ema(candles.close, 20)
        ema_50 = ema(candles.close, 50)
        trend = None
        if ema_10[-1] > ema_20[-1] > ema_50[-1]:
            trend = TradeType.long.name
        if ema_10[-1] < ema_20[-1] < ema_50[-1]:
            trend = TradeType.short.name
        if trend is not None:
            self._delete_last_in_progress_trade()
            self._start_new_trade(trend, candles.index[-1])

    def entry_signal(self, candles, day_candles=None):
        is_sqz = is_squeeze(candles)
        last_order_status = self._can_open_new_trade()
        if last_order_status.ready_to_procceed \
                and last_order_status.is_long \
                and not is_sqz:
            return self._update_open_trade(TradeType.long.name, candles.close[-1], "ema_34", 0, candles.index[-1])
            # say_something(f"{self.symbol} open {TradeType.long.name}")

        if last_order_status.ready_to_procceed \
                and last_order_status.is_short \
                and not is_sqz:
            return self._update_open_trade(TradeType.short.name, candles.close[-1], "ema_34", 0, candles.index[-1])
            # say_something(f"{self.symbol} open {TradeType.short.name}")

    def exit_signal(self, candles, day_candles=None):
        last_order_status = self._can_close_trade()
        is_profit, take_profit = self._is_take_profit(candles)
        is_loss, stop_loss = self._is_stop_loss(candles)
        ema_50 = ema(candles.close, 50)
        is_sqz = is_squeeze(candles)
        if last_order_status.ready_to_procceed and last_order_status.is_long \
                and (is_loss or is_profit or is_sqz):
            return self._update_close_trade(
                TradeType.short.name,
                candles.close[-1],
                "ema_34",
                ema_50[-1],
                candles.index[-1],
                is_profit,
                is_loss,
                take_profit,
                stop_loss,
            )

        if last_order_status.ready_to_procceed and last_order_status.is_short \
                and (is_loss or is_profit or is_sqz):
            return self._update_close_trade(
                TradeType.long.name,
                candles.close[-1],
                "ema_34",
                ema_50[-1],
                candles.index[-1],
                is_profit,
                is_loss,
                take_profit,
                stop_loss,
            )
