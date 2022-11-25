import logging

from pandas_ta import stoch

from ..indicator.utils import TradeType
from ..indicator.logistic_regression import predict_xgb_next_ticker
from .abc_strategy import ABCStrategy

log = logging.getLogger(__name__)


class LogisticRegressionStrategy(ABCStrategy):
    strategy_name = "logistic regression strategy"

    def __init__(self, symbol: str):
        self.symbol = symbol

    def seek_trend(self, candles, day_candles=None):
        stoch_data = stoch(candles.high, candles.low, candles.close)
        stoch_k = stoch_data["STOCHk_14_3_3"]
        stoch_d = stoch_data["STOCHd_14_3_3"]
        if (stoch_d[-2] < 20) and stoch_k[-1] > 20 and stoch_d[-1] > 20:
            self._delete_last_in_progress_trade()
            self._start_new_trade(TradeType.long.name, candles.index[-1], h4_date=day_candles.index[-1])
        if (stoch_d[-2] > 80) and stoch_k[-1] < 80 and stoch_d[-1] < 80:
            self._delete_last_in_progress_trade()
            self._start_new_trade(TradeType.short.name, candles.index[-1], h4_date=day_candles.index[-1])


    def entry_signal(self, candles, day_candles=None) -> bool:
        last_order_status = self._can_open_new_trade()
        action, accuracy, _ = self._get_open_signal(candles, for_trend=False)
        if last_order_status.ready_to_procceed and last_order_status.is_long and action is TradeType.long.name:
            return self._update_open_trade(
                TradeType.long.name, candles.close[-1], self.strategy_name, 0, candles.index[-1]
            )
        if last_order_status.ready_to_procceed and last_order_status.is_short and action is TradeType.short.name:
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
        trend, accuracy, features = predict_xgb_next_ticker(candles.copy(deep=True), predict_step=1, for_trend=for_trend)
        most_important_feature = max(features, key=lambda f: f["Importance"])
        print(accuracy)
        if trend is None:
            return None, 0, 0
        if trend[0] > 0.5:
            return TradeType.long.name, trend[0], most_important_feature["Feature"]
        elif trend[0] < 0.5:
            return TradeType.short.name, trend[0], most_important_feature["Feature"]
        return None, 0, 0
