import logging

from pandas_ta import supertrend

from ..chart.heikin_ashi import heikin_ashi
from ..indicator.utils import TradeType
from .abc_strategy import ABCStrategy

log = logging.getLogger(__name__)


class HeikinAshiSupperTrendStrategy(ABCStrategy):
    strategy_name = "heikin ashi supper trend strategy"

    def __init__(self, symbol: str):
        self.symbol = symbol

    def seek_trend(self, candles, day_candles=None):
        super_trend = supertrend(candles.high, candles.low, candles.close, length=34, multiplier=3)["SUPERT_34_3.0"]
        close_price = candles.close[-1]
        self._delete_last_in_progress_trade()
        if super_trend[-1] < close_price:
            self._start_new_trade(TradeType.long.name, candles.index[-1])

        if super_trend[-1] > close_price:
            self._start_new_trade(TradeType.short.name, candles.index[-1])

    def entry_signal(self, candles, day_candles=None) -> bool:
        last_order_status = self._can_open_new_trade()
        ha_data = heikin_ashi(candles)
        open_price = ha_data.open
        close_price = ha_data.close
        if last_order_status.ready_to_procceed \
                and last_order_status.is_long\
                and open_price[-3] > close_price[-3] \
                and open_price[-2] > close_price[-2] \
                and open_price[-1] < close_price[-1]:
            return self._update_open_trade(
                TradeType.short.name, candles.close[-1], self.strategy_name, 0, candles.index[-1]
            )
        if last_order_status.ready_to_procceed \
                and last_order_status.is_short \
                and open_price[-3] < close_price[-3] \
                and open_price[-2] < close_price[-2] \
                and open_price[-1] > close_price[-1]:
            return self._update_open_trade(
                TradeType.short.name, candles.close[-1], self.strategy_name, 0, candles.index[-1]
            )

    def exit_signal(self, candles, day_candles=None) -> bool:
        last_order_status = self._can_close_trade()
        is_profit, take_profit = self._is_take_profit(candles)
        is_loss, stop_loss = self._is_stop_loss(candles)
        ha_data = heikin_ashi(candles)
        open_price = ha_data.open
        close_price = ha_data.close
        if last_order_status.ready_to_procceed \
                and last_order_status.is_long \
                and (is_profit or is_loss or close_price[-1] < open_price[-1]):
            return self._update_close_trade(
                TradeType.long.name,
                candles.close[-1],
                self.strategy_name,
                candles.close[-1],
                candles.index[-1],
                is_profit,
                is_loss,
                take_profit,
                stop_loss,
            )

        if last_order_status.ready_to_procceed \
                and last_order_status.is_short \
                and (is_profit or is_loss or close_price[-1] > open_price[-1]):
            return self._update_close_trade(
                TradeType.short.name,
                candles.close[-1],
                self.strategy_name,
                candles.close[-1],
                candles.index[-1],
                is_profit,
                is_loss,
                take_profit,
                stop_loss,
            )
