import logging
from pandas_ta.momentum import macd, stochrsi
from pandas_ta.overlap import ichimoku

from .abc_strategy import ABCStrategy
from ..indicator.logistic_regression import predict_xgb_next_ticker
from ..indicator.utils import TradeType

log = logging.getLogger(__name__)


class MacdHistogramStrategy(ABCStrategy):
    strategy_name = "macd histogram strategy"

    def __init__(self, symbol: str):
        ABCStrategy.__init__(self, symbol)

    def seek_trend(self, candles, day_candles=None):
        trend, accuracy, _ = self._get_open_signal(candles)
        self._delete_last_in_progress_trade()
        if trend is not None:
            self._start_new_trade(trend, candles.index[-1], open_type="ichimoku",
                                  h4_date=day_candles.index[-1])
            return

    def entry_signal(self, candles, day_candles=None):
        last_order_status = self._can_open_new_trade()
        if (
                last_order_status.ready_to_procceed
                and last_order_status.is_long
        ):
            macd_histogram, stock_rsi_d, stock_rsi_k = self._get_signals(candles)
            if (
                    ((macd_histogram[-1] <= 0 or macd_histogram[-2] < 0 < macd_histogram[-1])
                     and macd_histogram[-2] <= macd_histogram[-1]
                     and stock_rsi_k[-1] > stock_rsi_d[-1])
                    or (0 < macd_histogram[-3] > macd_histogram[-2] and macd_histogram[-2] * 2 < macd_histogram[-1] > 0
                        and stock_rsi_k[-1] > stock_rsi_d[-1]
                        and stock_rsi_k[-2] <= stock_rsi_d[-2])
                    # or (
                    #     stock_rsi_k[-1] > stock_rsi_d[-1]
                    #     and stock_rsi_k[-2] <= stock_rsi_d[-2])
            ):
                return self._update_open_trade(
                    TradeType.long.name, candles.close[-1], "macd_ichimoku", macd_histogram[-1], candles.index[-1]
                )
        if (
                last_order_status.ready_to_procceed
                and last_order_status.is_short
        ):
            macd_histogram, stock_rsi_d, stock_rsi_k = self._get_signals(candles)
            if (
                    ((macd_histogram[-1] >= 0 or macd_histogram[-2] > 0 > macd_histogram[-1])
                     and macd_histogram[-2] >= macd_histogram[-1]
                     and stock_rsi_k[-1] < stock_rsi_d[-1])
                    or (0 > macd_histogram[-3] < macd_histogram[-2] and macd_histogram[-2] * 2 > macd_histogram[-1] < 0
                        and stock_rsi_k[-1] < stock_rsi_d[-1]
                        and stock_rsi_k[-2] >= stock_rsi_d[-2])
                    # or (stock_rsi_k[-1] < stock_rsi_d[-1]
                    #     and stock_rsi_k[-2] >= stock_rsi_d[-2])
            ):
                return self._update_open_trade(
                    TradeType.short.name, candles.close[-1], "macd_ichimoku", macd_histogram[-1], candles.index[-1]
                )

        return False

    def exit_signal(self, candles, day_candles=None):
        last_order_status = self._can_close_trade()
        trend, _, _ = self._get_open_signal(candles)

        if last_order_status.ready_to_procceed and last_order_status.is_long:
            macd_histogram, stock_rsi_d, stock_rsi_k = self._get_signals(candles)
            is_profit, take_profit = self._is_take_profit(candles)
            is_loss, stop_loss = self._is_stop_loss(candles)
            if (
                    (macd_histogram[-1] >= 0 and macd_histogram[-1] < macd_histogram[-2] and stock_rsi_k[-1] < stock_rsi_d[-1])
                    or is_profit
                    or is_loss
                    or trend is not TradeType.long.name
            ):
                return self._update_close_trade(
                    TradeType.short.name,
                    candles.close[-1],
                    "macd_ichimoku",
                    macd_histogram[-1],
                    candles.index[-1],
                    is_profit,
                    is_loss,
                    take_profit,
                    stop_loss,
                )
        if last_order_status.ready_to_procceed and last_order_status.is_short:
            macd_histogram, stock_rsi_d, stock_rsi_k = self._get_signals(candles)
            is_profit, take_profit = self._is_take_profit(candles)
            is_loss, stop_loss = self._is_stop_loss(candles)
            if (
                    (macd_histogram[-1] <= 0 and macd_histogram[-1] > macd_histogram[-2] and stock_rsi_k[-1] > stock_rsi_d[-1])
                    or is_profit
                    or is_loss
                    or trend is not TradeType.short.name
            ):
                return self._update_close_trade(
                    TradeType.long.name,
                    candles.close[-1],
                    "macd_ichimoku",
                    macd_histogram[-1],
                    candles.index[-1],
                    is_profit,
                    is_loss,
                    take_profit,
                    stop_loss,
                )
        return False

    def _get_signals(self, candles):
        close = candles.close  # kalman_candles(candles).close
        macd_data = macd(close, 13, 34)
        macd_histogram = macd_data["MACDh_13_34_9"]
        stoch_rsi_data = stochrsi(close)
        stock_rsi_k = stoch_rsi_data["STOCHRSIk_14_14_3_3"]
        stock_rsi_d = stoch_rsi_data["STOCHRSId_14_14_3_3"]
        return macd_histogram, stock_rsi_d, stock_rsi_k

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
