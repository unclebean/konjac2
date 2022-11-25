from pandas_ta import ema, macd
from .abc_strategy import ABCStrategy
from ..indicator.logistic_regression import predict_xgb_next_ticker
from ..indicator.utils import TradeType


class EmaMacdStrategy(ABCStrategy):
    strategy_name = "ema macd"

    def __init__(self, symbol: str):
        ABCStrategy.__init__(self, symbol)

    def seek_trend(self, candles, day_candles=None):
        trend, accuracy, _ = self._get_open_signal(candles)
        self._delete_last_in_progress_trade()
        if trend is not None:
            self._start_new_trade(trend, candles.index[-1])

    def entry_signal(self, candles, day_candles=None):
        last_order_status = self._can_open_new_trade()
        macd_data = macd(candles.close, 13, 34)
        macd_ = macd_data["MACD_13_34_9"]
        macd_signal = macd_data["MACDs_13_34_9"]
        macd_histogram = macd_data["MACDh_13_34_9"]
        if last_order_status.ready_to_procceed and last_order_status.is_long \
                and macd_[-1] > macd_signal[-1] \
                and macd_[-2] < macd_signal[-2] \
                and macd_histogram[-1] < 0:
            return self._update_open_trade(TradeType.long.name, candles.close[-1], self.strategy_name, macd_[-1], candles.index[-1])
        if last_order_status.ready_to_procceed and last_order_status.is_short \
                and macd_[-1] < macd_signal[-1] \
                and macd_[-2] > macd_signal[-2] \
                and macd_histogram[-1] > 0:
            return self._update_open_trade(TradeType.short.name, candles.close[-1], self.strategy_name, macd_[-1], candles.index[-1])

    def exit_signal(self, candles, day_candles=None):
        last_order_status = self._can_close_trade()
        is_profit, take_profit = self._is_take_profit(candles)
        is_loss, stop_loss = self._is_stop_loss(candles)
        macd_data = macd(candles.close, 13, 34)
        macd_ = macd_data["MACD_13_34_9"]
        macd_signal = macd_data["MACDs_13_34_9"]
        macd_histogram = macd_data["MACDh_13_34_9"]

        if last_order_status.ready_to_procceed and last_order_status.is_long \
                and (is_loss or is_profit
                     or (macd_[-1] < macd_signal[-1] and macd_[-2] > macd_signal[-2])):
            return self._update_close_trade(
                TradeType.short.name,
                candles.close[-1],
                "macd_rsi",
                candles.close[-1],
                candles.index[-1],
                is_profit,
                is_loss,
                take_profit,
                stop_loss,
            )

        if last_order_status.ready_to_procceed and last_order_status.is_short \
                and (is_loss or is_profit
                     or (macd_[-1] > macd_signal[-1] and macd_[-2] < macd_signal[-2])):
            return self._update_close_trade(
                TradeType.long.name,
                candles.close[-1],
                "macd_rsi",
                candles.close[-1],
                candles.index[-1],
                is_profit,
                is_loss,
                take_profit,
                stop_loss,
            )

    def _get_open_signal(self, candles):
        trend, accuracy, features = predict_xgb_next_ticker(candles.copy(deep=True), predict_step=3)
        most_important_feature = max(features, key=lambda f: f["Importance"])
        if trend is None:
            return None, 0, 0
        if trend[0] > 0.5 and trend[1] > 0.5 and trend[2] > 0.5:
            return TradeType.long.name, trend[0], most_important_feature["Feature"]
        elif trend[0] < 0.5 and trend[1] < 0.5 and trend[2] < 0.5:
            return TradeType.short.name, trend[0], most_important_feature["Feature"]
        return None, 0, 0

