from ..indicator.utils import TradeType
from ..indicator.logistic_regression import LogisticRegressionModel, predict_xgb_next_ticker
from ..models.trade import TradeStatus
from .abc_strategy import ABCStrategy


class LogisticRegressionStrategy(ABCStrategy):
    strategy_name = "logistic regression strategy"

    def __init__(self, symbol: str):
        self.symbol = symbol

    def seek_trend(self, candles):
        last_trade = self.get_trade()
        if last_trade is None or last_trade.status == TradeStatus.closed.name:
            self._start_new_trade(TradeType.long.name, candles.index[-1])

    def entry_signal(self, candles):
        last_trade = self.get_trade()
        if last_trade is not None and last_trade.status == TradeStatus.in_progress.name:
            trend, accuracy = self._get_signal(candles)
            if trend is not None and trend == TradeType.long.name:
                self._update_open_trade(last_trade.trend, candles.close[-1], "lr", accuracy, candles.index[-1])

    def exit_signal(self, candles):
        last_trade = self.get_trade()
        if (
            last_trade is not None
            and last_trade.status == TradeStatus.opened.name
            and last_trade.entry_date != candles.index[-1]
        ):
            last_trade = self.get_trade()
            position = last_trade.opened_position
            close_price = candles.close[-1]
            change_pctg = (close_price - position) / position
            trend, accuracy = self._get_signal(candles)
            # if change_pctg > 0.004 or change_pctg < -0.004:
            if (trend != last_trade.trend and trend is not None) or change_pctg > 0.005 or change_pctg < -0.005:
                self._update_close_trade(TradeType.short.name, close_price, "lr", accuracy, candles.index[-1])

    def _get_signal(self, candles):
        trend, accuracy = LogisticRegressionModel(candles.copy(deep=True))
        if trend[0] > 0.5:
            return TradeType.long.name, accuracy
        elif trend[0] < 0.5:
            return TradeType.short.name, accuracy
        return None, 0
