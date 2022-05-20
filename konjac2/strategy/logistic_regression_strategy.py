from pandas_ta.overlap import dema, ichimoku

from ..indicator.utils import TradeType
from ..indicator.logistic_regression import predict_xgb_next_ticker
from ..models.trade import TradeStatus
from .abc_strategy import ABCStrategy


class LogisticRegressionStrategy(ABCStrategy):
    strategy_name = "logistic regression strategy"

    def __init__(self, symbol: str):
        self.symbol = symbol

    def seek_trend(self, candles):
        dema144 = dema(candles.close, 144)[-1]
        dema169 = dema(candles.close, 169)[-1]

        ichimoku_df, _ = ichimoku(candles.high, candles.low, candles.close)
        span_a = ichimoku_df["ISA_9"][-1]
        span_b = ichimoku_df["ISB_26"][-1]
        # kijun_sen = ichimoku_df["ITS_9"][-1]
        # tenkan_sen = ichimoku_df["IKS_26"][-1]
        close_price = candles.close[-1]
        trend = None
        if close_price > span_a and close_price > span_b and close_price > dema144 and close_price > dema169:
            trend = TradeType.long.name
        if close_price < span_a and close_price < span_b and close_price < dema144 and close_price < dema169:
            trend = TradeType.short.name
        self._delete_last_in_progress_trade()
        if trend is not None:
            self._start_new_trade(trend, candles.index[-1])

    def entry_signal(self, candles) -> bool:
        last_trade = self.get_trade()
        if last_trade is not None and last_trade.status == TradeStatus.in_progress.name:
            trend, accuracy = self._get_signal(candles)
            if trend is not None and trend == last_trade.trend:
                return self._update_open_trade(last_trade.trend, candles.close[-1], "lr", accuracy, candles.index[-1])

    def exit_signal(self, candles) -> bool:
        last_trade = self.get_trade()
        if (
            last_trade is not None
            and last_trade.status == TradeStatus.opened.name
            and last_trade.entry_date != candles.index[-1]
        ):
            close_price = candles.close[-1]
            trend, accuracy = self._get_signal(candles)
            result = (
                last_trade.opened_position - close_price
                if last_trade.trend == TradeType.short.name
                else close_price - last_trade.opened_position
            ) * last_trade.quantity
            # order_running_hours = (candles.index[-1] - last_trade.entry_date).seconds / 3600
            take_profit = last_trade.opened_position * last_trade.quantity * 0.02
            stop_loss = last_trade.opened_position * last_trade.quantity * 0.01
            print("result {} profit {} loss {}".format(result, take_profit, stop_loss))
            if (
                (trend != last_trade.trend and trend is not None)
                or (result > 0 and result > take_profit)
                or (result < 0 and abs(result) > stop_loss)
            ):
                return self._update_close_trade(
                    trend, close_price, "lr", accuracy, candles.index[-1], take_profit, stop_loss
                )

    def _get_signal(self, candles):
        trend, accuracy = predict_xgb_next_ticker(candles.copy(deep=True))
        if trend is None:
            return None, 0
        if trend[0] > 0.5:
            return TradeType.long.name, accuracy
        elif trend[0] < 0.5:
            return TradeType.short.name, accuracy
        return None, 0
