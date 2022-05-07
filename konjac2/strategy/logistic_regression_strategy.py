from ..indicator.utils import TradeType
from ..indicator.logistic_regression import LogisticRegressionModel
from ..models.trade import TradeStatus
from .abc_strategy import ABCStrategy


class LogisticRegressionStrategy(ABCStrategy):
    strategy_name = "logistic regression strategy"

    def __init__(self, symbol: str):
        self.symbol = symbol

    def seek_trend(self, candles):
        last_trade = self.get_trade()
        if last_trade is None or last_trade.status == TradeStatus.closed.name:
            trend, _ = LogisticRegressionModel(candles.copy(deep=True))
            trend = TradeType.long.name if trend[0] > 0.5 else TradeType.short.name
            if trend == TradeType.long.name:
                self._start_new_trade(trend, candles.index[-1])

    def entry_signal(self, candles):
        last_trade = self.get_trade()
        if last_trade is not None and last_trade.status == TradeStatus.in_progress.name:
            self._update_open_trade(last_trade.trend, candles.close[-1], "lr", "", candles.index[-1])

    def exit_signal(self, candles):
        last_trade = self.get_trade()
        if last_trade is not None and last_trade.status == TradeStatus.opened.name:
            last_trade = self.get_trade()
            position = last_trade.opened_position
            close_price = candles.close[-1]
            change_pctg = (close_price - position) / position

            trend, _ = LogisticRegressionModel(candles.copy(deep=True))
            trend = TradeType.long.name if trend[0] > 0.5 else TradeType.short.name
            if change_pctg > 0.008 or change_pctg < -0.004:
                self._update_close_trade(trend, candles.close[-1], "lr", "", candles.index[-1])
