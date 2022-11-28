import logging

from pandas_ta.momentum import macd
from .abc_strategy import ABCStrategy
from ..chart.heikin_ashi import heikin_ashi
from ..indicator.utils import TradeType

log = logging.getLogger(__name__)


class MacdStrategy(ABCStrategy):
    strategy_name = "macd"

    def __init__(self, symbol: str, trade_short_order=True):
        ABCStrategy.__init__(self, symbol, trade_short_order)

    def seek_trend(self, candles, day_candles=None):
        ha_data = heikin_ashi(candles)
        open_price = ha_data.open
        close_price = ha_data.close
        self._delete_last_in_progress_trade()
        if close_price[-1] > open_price[-1]:
            self._start_new_trade(TradeType.long.name, candles.index[-1], open_type="ichimoku",
                                  h4_date=day_candles.index[-1])
        if close_price[-1] < open_price[-1] and self.trade_short_order:
            self._start_new_trade(TradeType.short.name, candles.index[-1], open_type="ichimoku",
                                  h4_date=day_candles.index[-1])

    def entry_signal(self, candles, day_candles=None):
        last_order_status = self._can_open_new_trade()
        macd_data = macd(candles.close)
        macd_ = macd_data["MACD_12_26_9"]
        signal_ = macd_data["MACDs_12_26_9"]

        if last_order_status.ready_to_procceed \
                and last_order_status.is_long \
                and macd_[-2] <= signal_[-2] \
                and macd_[-1] > signal_[-1]:
            return self._update_open_trade(
                TradeType.long.name, candles.close[-1], "macd_vwap", 0, candles.index[-1]
            )
        if last_order_status.ready_to_procceed \
                and last_order_status.is_short \
                and macd_[-2] >= signal_[-2] \
                and macd_[-1] < signal_[-1]:
            return self._update_open_trade(
                TradeType.short.name, candles.close[-1], "macd_vwap", 0, candles.index[-1]
            )

        return False

    def exit_signal(self, candles, day_candles=None):
        last_order_status = self._can_close_trade()
        macd_data = macd(candles.close)
        macd_ = macd_data["MACD_12_26_9"]
        signal_ = macd_data["MACDs_12_26_9"]
        is_profit, take_profit = self._is_take_profit(candles)
        is_loss, stop_loss = self._is_stop_loss(candles)

        if last_order_status.ready_to_procceed and last_order_status.is_long \
                and (
                macd_[-1] < signal_[-1]
                or is_profit
                or is_loss
        ):
            return self._update_close_trade(
                TradeType.short.name,
                candles.close[-1],
                "macd",
                macd_[-1],
                candles.index[-1],
                is_profit,
                is_loss,
                take_profit,
                stop_loss,
            )
        if last_order_status.ready_to_procceed and last_order_status.is_short \
                and (
                macd_[-1] > signal_[-1]
                or is_profit
                or is_loss
        ):
            return self._update_close_trade(
                TradeType.long.name,
                candles.close[-1],
                "macd",
                macd_[-1],
                candles.index[-1],
                is_profit,
                is_loss,
                take_profit,
                stop_loss,
            )
        return False
