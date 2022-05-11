from pandas_ta.overlap import dema

from ..bot.telegram_bot import say_something
from ..indicator.utils import TradeType
from ..indicator.logistic_regression import predict_xgb_next_ticker
from ..models.trade import TradeStatus
from .abc_strategy import ABCStrategy


class LogisticRegressionStrategy(ABCStrategy):
    strategy_name = "logistic regression strategy"

    def __init__(self, symbol: str):
        self.symbol = symbol

    def seek_trend(self, candles):
        dema144 = dema(candles.close)[-1]
        dema169 = dema(candles.close)[-1]
        close_price = candles.close[-1]
        trend = None
        if close_price > dema144 and close_price > dema169:
            trend = TradeType.long.name
        if close_price < dema144 and close_price < dema169:
            trend = TradeType.short.name
        if trend is not None:
            self._delete_last_in_progress_trade()
            self._start_new_trade(trend, candles.index[-1])

    def entry_signal(self, candles):
        last_trade = self.get_trade()
        if last_trade is not None and last_trade.status == TradeStatus.in_progress.name:
            trend, accuracy = self._get_signal(candles)
            if trend is not None and trend == last_trade.trend:
                self._update_open_trade(last_trade.trend, candles.close[-1], "lr", accuracy, candles.index[-1])

    def exit_signal(self, candles):
        last_trade = self.get_trade()
        if (
            last_trade is not None
            and last_trade.status == TradeStatus.opened.name
            and last_trade.entry_date != candles.index[-1]
        ):
            close_price = candles.close[-1]
            trend, accuracy = self._get_signal(candles)
            say_something("{} exit signal {} accuracy {}".format(self.symbol, trend, accuracy))
            if trend != last_trade.trend and trend is not None:  # or change_pctg > 0.005 or change_pctg < -0.005:
                self._update_close_trade(trend, close_price, "lr", accuracy, candles.index[-1])

    def _get_signal(self, candles):
        trend, accuracy = predict_xgb_next_ticker(candles.copy(deep=True))
        if trend is None:
            return None, 0
        if trend[0] > 0.5:
            return TradeType.long.name, accuracy
        elif trend[0] < 0.5:
            return TradeType.short.name, accuracy
        return None, 0
