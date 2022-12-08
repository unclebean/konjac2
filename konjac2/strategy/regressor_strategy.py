import logging

from ..indicator.regressor import regressor_predict, logistic_predict
from ..indicator.utils import TradeType
from .abc_strategy import ABCStrategy

log = logging.getLogger(__name__)


class RegressorStrategy(ABCStrategy):
    strategy_name = "regressor strategy"

    def __init__(self, symbol: str):
        self.symbol = symbol

    def seek_trend(self, candles, day_candles=None):
        action = logistic_predict(candles.copy(deep=True))
        if action is TradeType.long.name:
            self._delete_last_in_progress_trade()
            self._start_new_trade(action, candles.index[-1], h4_date=day_candles.index[-1])
        if action is TradeType.short.name:
            self._delete_last_in_progress_trade()
            self._start_new_trade(action, candles.index[-1], h4_date=day_candles.index[-1])

    def entry_signal(self, candles, day_candles=None) -> bool:
        last_order_status = self._can_open_new_trade()
        if last_order_status.ready_to_procceed and last_order_status.is_long:
            return self._update_open_trade(
                TradeType.long.name, candles.close[-1], self.strategy_name, 0, candles.index[-1]
            )
        if last_order_status.ready_to_procceed and last_order_status.is_short:
            return self._update_open_trade(
                TradeType.short.name, candles.close[-1], self.strategy_name, 0, candles.index[-1]
            )

    def exit_signal(self, candles, day_candles=None) -> bool:
        last_order_status = self._can_close_trade()
        is_profit, take_profit = self._is_take_profit(candles)
        is_loss, stop_loss = self._is_stop_loss(candles)
        action = logistic_predict(candles)
        if last_order_status.ready_to_procceed \
                and last_order_status.is_long \
                and (is_profit or is_loss):
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
                and (is_profit or is_loss):
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
