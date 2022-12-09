import logging

from pandas_ta import rsi
from pandas_ta.momentum import cci

from .abc_strategy import ABCStrategy
from ..indicator.utils import TradeType

log = logging.getLogger(__name__)


class RSICCIStrategy(ABCStrategy):
    strategy_name = "rsi cci"

    def __init__(self, symbol: str, trade_short_order=True):
        ABCStrategy.__init__(self, symbol, trade_short_order)

    def seek_trend(self, candles, day_candles=None):
        rsi_data = rsi(candles.close, length=30)
        trend = None
        if rsi_data[-1] > 50:
            trend = TradeType.long.name
        if rsi_data[-1] < 50 and self.trade_short_order:
            trend = TradeType.short.name
        if trend is not None:
            self._delete_last_in_progress_trade()
            self._start_new_trade(trend, candles.index[-1])

    def entry_signal(self, candles, day_candles=None):
        cci20 = cci(candles.high, candles.low, candles.close, 20)
        last_order_status = self._can_open_new_trade()
        if last_order_status.ready_to_procceed \
                and last_order_status.is_long \
                and cci20[-2] < -100 < cci20[-1]:
            return self._update_open_trade(TradeType.long.name, candles.close[-1], "cci_20", 0, candles.index[-1])
            # say_something(f"{self.symbol} open {TradeType.long.name}")

        if last_order_status.ready_to_procceed \
                and last_order_status.is_short \
                and cci20[-2] > 100 > cci20[-1]:
            return self._update_open_trade(TradeType.short.name, candles.close[-1], "cci_20", 0, candles.index[-1])
            # say_something(f"{self.symbol} open {TradeType.short.name}")

    def exit_signal(self, candles, day_candles=None):
        last_order_status = self._can_close_trade()
        is_profit, take_profit = self._is_take_profit(candles)
        is_loss, stop_loss = self._is_stop_loss(candles)
        cci20 = cci(candles.high, candles.low, candles.close, 20)
        if last_order_status.ready_to_procceed and last_order_status.is_long \
                and (cci20[-1] > 200 or is_loss or is_profit):
            return self._update_close_trade(
                TradeType.short.name,
                candles.close[-1],
                "cci_20",
                cci20[-1],
                candles.index[-1],
                is_profit,
                is_loss,
                take_profit,
                stop_loss,
            )

        if last_order_status.ready_to_procceed and last_order_status.is_short \
                and (cci20[-1] < -200 or is_loss or is_profit):
            return self._update_close_trade(
                TradeType.long.name,
                candles.close[-1],
                "cci_20",
                cci20[-1],
                candles.index[-1],
                is_profit,
                is_loss,
                take_profit,
                stop_loss,
            )
