import logging

from pandas_ta.momentum import macd
from .abc_strategy import ABCStrategy
from ..indicator.utils import TradeType

log = logging.getLogger(__name__)


class MacdStrategy(ABCStrategy):
    strategy_name = "macd"

    def __init__(self, symbol: str):
        ABCStrategy.__init__(self, symbol)

    def seek_trend(self, candles, day_candles=None):
        macd_data = macd(candles.close)
        macd_ = macd_data["MACD_12_26_9"]
        self._delete_last_in_progress_trade()

        if macd_[-2] < 0 < macd_[-1]:
            self._start_new_trade(TradeType.short.name, candles.index[-1], open_type="ichimoku",
                                  h4_date=day_candles.index[-1])
        if macd_[-2] > 0 > macd_[-1]:
            self._start_new_trade(TradeType.long.name, candles.index[-1], open_type="ichimoku",
                                  h4_date=day_candles.index[-1])

    def entry_signal(self, candles, day_candles=None):
        last_order_status = self._can_open_new_trade()

        if last_order_status.ready_to_procceed \
                and last_order_status.is_long:
            return self._update_open_trade(
                TradeType.long.name, candles.close[-1], "macd_vwap", 0, candles.index[-1]
            )
        if last_order_status.ready_to_procceed \
                and last_order_status.is_short:
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
                is_profit
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
                is_profit
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
