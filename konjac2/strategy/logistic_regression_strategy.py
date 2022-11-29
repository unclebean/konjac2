import logging

from ..indicator.utils import TradeType
from ..indicator.logistic_regression import predict_xgb_next_ticker
from .abc_strategy import ABCStrategy

log = logging.getLogger(__name__)


class LogisticRegressionStrategy(ABCStrategy):
    strategy_name = "logistic regression strategy"

    def __init__(self, symbol: str):
        self.symbol = symbol

    def seek_trend(self, candles, day_candles=None):
        if candles.index[-1].hour != 8:
            return
        action, accuracy, _ = self._get_open_signal(day_candles, for_trend=True)
        if action is TradeType.long.name and day_candles.close[-1] > day_candles.open[-1]:
            self._delete_last_in_progress_trade()
            self._start_new_trade(action, candles.index[-1], h4_date=day_candles.index[-1])
        if action is TradeType.short.name and day_candles.close[-1] < day_candles.open[-1]:
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

    def _get_open_signal(self, candles, for_trend=True):
        trend, accuracy, features = predict_xgb_next_ticker(candles.copy(deep=True), predict_step=0,
                                                            for_trend=for_trend)
        most_important_feature = max(features, key=lambda f: f["Importance"])
        if trend is None:
            return None, 0, 0
        if trend[-1] > 0.5:
            return TradeType.long.name, trend[0], most_important_feature["Feature"]
        elif trend[-1] < 0.5:
            return TradeType.short.name, trend[0], most_important_feature["Feature"]
        return None, 0, 0
