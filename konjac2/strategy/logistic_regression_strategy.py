from pandas_ta.overlap import ema
from pandas_ta.volume import obv

from ..indicator.utils import TradeType
from ..indicator.logistic_regression import predict_xgb_next_ticker
from ..models.trade import TradeStatus
from .abc_strategy import ABCStrategy


class LogisticRegressionStrategy(ABCStrategy):
    strategy_name = "logistic regression strategy"

    def __init__(self, symbol: str):
        self.symbol = symbol

    def seek_trend(self, candles):
        obv_values = obv(candles.close, candles.volume)
        obv_ema200 = ema(obv_values, 200)
        ema12 = ema(candles.close, 12)

        trend = None
        if obv_values[-1] > obv_ema200[-1] and obv_values[-2] > obv_ema200[-2] and candles.close[-1] > ema12[-1]:
            trend = TradeType.long.name
        if obv_values[-1] < obv_ema200[-1] and obv_values[-2] < obv_ema200[-2] and candles.close[-1] < ema12[-1]:
            trend = TradeType.short.name

        self._delete_last_in_progress_trade()
        if trend is not None:
            self._start_new_trade(trend, candles.index[-1])

    def entry_signal(self, candles) -> bool:
        last_trade = self.get_trade()
        if last_trade is not None and last_trade.status == TradeStatus.in_progress.name:
            trend, accuracy, _ = self._get_open_signal(candles)
            if trend is not None and trend == last_trade.trend:
                return self._update_open_trade(
                    last_trade.trend, candles.close[-1], 'lr', accuracy, candles.index[-1]
                )

    def exit_signal(self, candles) -> bool:
        last_trade = self.get_trade()
        if (
            last_trade is not None
            and last_trade.status == TradeStatus.opened.name
            and last_trade.entry_date != candles.index[-1]
        ):
            close_price = candles.close[-1]
            trend, accuracy, _ = self._get_signal(candles)
            # order_running_hours = (candles.index[-1] - last_trade.entry_date).seconds / 3600

            # result = (
            #     last_trade.opened_position - close_price
            #     if last_trade.trend == TradeType.short.name
            #     else close_price - last_trade.opened_position
            # ) * last_trade.quantity

            is_profit, take_profit = self._is_take_profit(candles)
            is_loss, stop_loss = self._is_stop_loss(candles)
            if (trend != last_trade.trend) or is_profit or is_loss:
                return self._update_close_trade(
                    trend,
                    close_price,
                    "lr",
                    accuracy,
                    candles.index[-1],
                    is_profit,
                    is_loss,
                    take_profit,
                    stop_loss,
                )

    def _get_open_signal(self, candles):
        trend, accuracy, features = predict_xgb_next_ticker(candles.copy(deep=True))
        most_important_feature = max(features, key=lambda f: f["Importance"])
        if trend is None:
            return None, 0, 0
        # if trend[0] > 0.55 and trend[0] < 0.75:
        if trend[0] > 0.6 and trend[0] < 0.8:
            return TradeType.long.name, trend[0], most_important_feature["Feature"]
        # elif trend[0] < 0.45 and trend[0] > 0.25:
        elif trend[0] < 0.4 and trend[0] > 0.2:
            return TradeType.short.name, trend[0], most_important_feature["Feature"]
        return None, 0, 0

    def _get_signal(self, candles):
        trend, accuracy, features = predict_xgb_next_ticker(candles.copy(deep=True))
        most_important_feature = max(features, key=lambda f: f["Importance"])
        if trend is None:
            return None, 0, 0
        # if trend[0] > 0.55 and trend[0] < 0.75:
        if trend[0] > 0.5 or trend[0] < 0.1:
            return TradeType.long.name, trend[0], most_important_feature["Feature"]
        # elif trend[0] < 0.45 and trend[0] > 0.25:
        elif trend[0] < 0.5 or trend[0] > 0.9:
            return TradeType.short.name, trend[0], most_important_feature["Feature"]
        return None, 0, 0
