import logging

from pandas_ta import bbands

from .abc_strategy import ABCStrategy
from ..indicator.senkou_span import senkou_span_a_b
from ..indicator.utils import TradeType

log = logging.getLogger(__name__)


class IchimokuBBStrategy(ABCStrategy):
    strategy_name = "ichimoku bb"

    def __init__(self, symbol: str, trade_short_order=True):
        ABCStrategy.__init__(self, symbol, trade_short_order)

    def seek_trend(self, candles, day_candles=None):
        close_price = day_candles.close[-1]
        isa, isb = senkou_span_a_b(day_candles.high, day_candles.low)
        is_long = close_price > isa[-26] and close_price > isb[-26]
        is_short = close_price < isa[-26] and close_price < isb[-26]
        trend = None
        if isa[-1] > isb[-1] > isb[-2] and isb[-2] < isa[-2] < isa[-1] and is_long:
            trend = TradeType.long.name
        if isa[-1] < isb[-1] and isa[-1] < isa[-2] < isb[-2] > isa[-2] and is_short:
            trend = TradeType.short.name
        if trend is not None:
            self._delete_last_in_progress_trade()
            self._start_new_trade(trend, candles.index[-1])

    def entry_signal(self, candles, day_candles=None):
        bb_20 = bbands(candles.close, 20)
        bb_20_low = bb_20["BBL_20_2.0"]
        bb_20_up = bb_20["BBU_20_2.0"]
        last_order_status = self._can_open_new_trade()
        if last_order_status.ready_to_procceed \
                and last_order_status.is_long \
                and bb_20_low[-2] > candles.close[-2] and bb_20_low[-1] < candles.close[-1]:
            return self._update_open_trade(TradeType.long.name, candles.close[-1], "ema_34", 0, candles.index[-1])
            # say_something(f"{self.symbol} open {TradeType.long.name}")

        if last_order_status.ready_to_procceed \
                and last_order_status.is_short \
                and bb_20_up[-2] < candles.close[-2] and bb_20_up[-1] > candles.close[-1]:
            return self._update_open_trade(TradeType.short.name, candles.close[-1], "ema_34", 0, candles.index[-1])
            # say_something(f"{self.symbol} open {TradeType.short.name}")

    def exit_signal(self, candles, day_candles=None):
        last_order_status = self._can_close_trade()
        is_profit, take_profit = self._is_take_profit(candles)
        is_loss, stop_loss = self._is_stop_loss(candles)
        isa, isb = senkou_span_a_b(day_candles.high, day_candles.low)
        if last_order_status.ready_to_procceed and last_order_status.is_long \
                and (isa[-2] == isa[-1] or isb[-2] == isb[-1] or is_loss or is_profit):
            return self._update_close_trade(
                TradeType.short.name,
                candles.close[-1],
                "isa",
                isa[-1],
                candles.index[-1],
                is_profit,
                is_loss,
                take_profit,
                stop_loss,
            )

        if last_order_status.ready_to_procceed and last_order_status.is_short \
                and (isa[-2] == isa[-1] or isb[-2] == isb[-1] or is_loss or is_profit):
            return self._update_close_trade(
                TradeType.long.name,
                candles.close[-1],
                "isa",
                isa[-1],
                candles.index[-1],
                is_profit,
                is_loss,
                take_profit,
                stop_loss,
            )
