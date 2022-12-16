import logging

from pandas_ta import ema
from pandas_ta.momentum import cci

from .abc_strategy import ABCStrategy
from ..chart.heikin_ashi import heikin_ashi
from ..indicator.utils import TradeType

log = logging.getLogger(__name__)


class CCIEMAStrategy(ABCStrategy):
    strategy_name = "cci_ema"

    def __init__(self, symbol: str, trade_short_order=True):
        ABCStrategy.__init__(self, symbol, trade_short_order)

    def seek_trend(self, candles, day_candles=None):
        ema_10 = ema(candles.close, 10)
        ema_30 = ema(candles.close, 30)
        trend = None
        if ema_10[-2] <= ema_30[-2] and ema_10[-1] > ema_30[-1]:
            trend = TradeType.long.name
        if ema_10[-2] >= ema_30[-2] and ema_10[-1] < ema_30[-1] and self.trade_short_order:
            trend = TradeType.short.name
        if trend is not None:
            self._delete_last_in_progress_trade()
            self._start_new_trade(trend, candles.index[-1])

    def entry_signal(self, candles, day_candles=None):
        cci7 = cci(candles.high, candles.low, candles.close, 7)
        ema_30 = ema(candles.close, 30)
        ha_data = heikin_ashi(candles)
        open_price = ha_data.open
        close_price = ha_data.close
        last_order_status = self._can_open_new_trade()
        if last_order_status.ready_to_procceed \
                and last_order_status.is_long \
                and ema_30[-1] < candles.close[-1] \
                and (cci7[-2] < -100 < cci7[-1] or cci7[-3] < -100 < cci7[-2]) \
                and close_price[-1] > open_price[-1]:
            return self._update_open_trade(TradeType.long.name, candles.close[-1], "ema_34", 0, candles.index[-1])
            # say_something(f"{self.symbol} open {TradeType.long.name}")

        if last_order_status.ready_to_procceed \
                and last_order_status.is_short \
                and ema_30[-1] > candles.close[-1] \
                and (cci7[-2] > 100 > cci7[-1] or cci7[-3] > 100 > cci7[-2])\
                and close_price[-1] < open_price[-1]:
            return self._update_open_trade(TradeType.short.name, candles.close[-1], "ema_34", 0, candles.index[-1])
            # say_something(f"{self.symbol} open {TradeType.short.name}")

    def exit_signal(self, candles, day_candles=None):
        last_order_status = self._can_close_trade()
        is_profit, take_profit = self._is_take_profit(candles)
        is_loss, stop_loss = self._is_stop_loss(candles)
        cci7 = cci(candles.high, candles.low, candles.close, 7)
        if last_order_status.ready_to_procceed and last_order_status.is_long \
                and (cci7[-1] > 200 or is_loss or is_profit):
            return self._update_close_trade(
                TradeType.short.name,
                candles.close[-1],
                "ema_34",
                cci7[-1],
                candles.index[-1],
                is_profit,
                is_loss,
                take_profit,
                stop_loss,
            )

        if last_order_status.ready_to_procceed and last_order_status.is_short \
                and (cci7[-1] < -200 or is_loss or is_profit):
            return self._update_close_trade(
                TradeType.long.name,
                candles.close[-1],
                "ema_34",
                cci7[-1],
                candles.index[-1],
                is_profit,
                is_loss,
                take_profit,
                stop_loss,
            )
