import logging
from pandas_ta.overlap import ema
from pandas_ta.volume import obv
from pandas_ta.momentum import stochrsi

from konjac2.indicator.squeeze_momentum import is_squeeze

from ..indicator.utils import TradeType
from ..indicator.logistic_regression import predict_xgb_next_ticker
from ..models.trade import TradeStatus
from .abc_strategy import ABCStrategy

log = logging.getLogger(__name__)


class LogisticRegressionStrategy(ABCStrategy):
    strategy_name = "logistic regression strategy"

    def __init__(self, symbol: str):
        self.symbol = symbol

    def seek_trend(self, candles, daily_candles):
        longer_timeframe_trend = self._get_longer_timeframe_volatility(candles, daily_candles)

        self._delete_last_in_progress_trade()
        if longer_timeframe_trend is not None:
            self._start_new_trade(longer_timeframe_trend, candles.index[-1])

    def entry_signal(self, candles, longer_timeframe_candles) -> bool:
        last_trade = self.get_trade()
        if last_trade is not None and last_trade.status == TradeStatus.in_progress.name:
            longer_timeframe_trend = self._get_longer_timeframe_volatility(candles, longer_timeframe_candles)
            trend, accuracy, _ = self._get_open_signal(candles)
            is_in_squeeze = is_squeeze(candles)
            if (
                trend is not None
                and trend == last_trade.trend
                and trend == longer_timeframe_trend
                and not is_in_squeeze
            ):
                status = self._update_open_trade(last_trade.trend, candles.close[-1], "lr", accuracy, candles.index[-1])
                _, take_profit = self._is_take_profit(candles)
                _, stop_loss = self._is_stop_loss(candles)
                log.info(f"open position for {self.symbol} take profit {take_profit} stop loss {stop_loss}")
                return status

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

            is_profit, take_profit = self._is_take_profit(candles)
            is_loss, stop_loss = self._is_stop_loss(candles)
            if (trend != last_trade.trend and trend is not None) or is_profit or is_loss:
                log.info(f"open position for {self.symbol} take profit {take_profit} stop loss {stop_loss}")
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
        if trend[0] > 0.5:
            return TradeType.long.name, trend[0], most_important_feature["Feature"]
        elif trend[0] < 0.5:
            return TradeType.short.name, trend[0], most_important_feature["Feature"]
        return None, 0, 0

    def _get_signal(self, candles):
        trend, accuracy, features = predict_xgb_next_ticker(candles.copy(deep=True))
        most_important_feature = max(features, key=lambda f: f["Importance"])
        if trend is None:
            return None, 0, 0
        if trend[0] > 0.5:
            return TradeType.long.name, trend[0], most_important_feature["Feature"]
        elif trend[0] < 0.5:
            return TradeType.short.name, trend[0], most_important_feature["Feature"]
        return None, 0, 0

    def _get_trend(self, candles):
        obv_values = obv(candles.close, candles.volume)
        obv_ema200 = ema(obv_values, 200)
        ema12 = ema(candles.close, 12)

        trend = None
        if obv_values[-1] > obv_ema200[-1] and obv_values[-2] > obv_ema200[-2] and candles.close[-1] > ema12[-1]:
            trend = TradeType.long.name
        if obv_values[-1] < obv_ema200[-1] and obv_values[-2] < obv_ema200[-2] and candles.close[-1] < ema12[-1]:
            trend = TradeType.short.name
        return trend

    def _get_stoch_rsi_trend(self, candles):
        stochrsi_values = stochrsi(candles.close, length=14, rsi_length=14, k=3, d=3)
        stochrsi_k = stochrsi_values["STOCHRSIk_14_14_3_3"]
        stoch_trend = None
        is_stoch_in_zone = False
        for k_value in reversed(stochrsi_k):
            if k_value > 80 and is_stoch_in_zone:
                stoch_trend = TradeType.short.name
                break
            if k_value < 20 and is_stoch_in_zone:
                stoch_trend = TradeType.long.name
                break
            if k_value > 20 and k_value < 80:
                is_stoch_in_zone = True
        return stoch_trend
