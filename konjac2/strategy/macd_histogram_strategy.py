import logging
from pandas_ta.momentum import macd, stochrsi

from .abc_strategy import ABCStrategy
from ..indicator.senkou_span import senkou_span_a_b
from ..indicator.utils import TradeType

log = logging.getLogger(__name__)


class MacdHistogramStrategy(ABCStrategy):
    strategy_name = "macd histogram strategy"

    def __init__(self, symbol: str):
        ABCStrategy.__init__(self, symbol)

    def seek_trend(self, candles, day_candles=None):
        macd_histogram, stock_rsi_d, stock_rsi_k = self._get_signals(candles)
        self._delete_last_in_progress_trade()
        if 0 < macd_histogram[-3] > macd_histogram[-2] and macd_histogram[-2] * 2 < macd_histogram[-1] > 0:
            self._start_new_trade(TradeType.long.name, candles.index[-1], open_type="volatility",
                                  h4_date=day_candles.index[-1])
        if 0 > macd_histogram[-3] < macd_histogram[-2] and macd_histogram[-2] * 2 > macd_histogram[-1] < 0:
            self._start_new_trade(TradeType.short.name, candles.index[-1], open_type="volatility",
                                  h4_date=day_candles.index[-1])


    def entry_signal(self, candles, day_candles=None):
        last_order_status = self._can_open_new_trade()
        if (
                last_order_status.ready_to_procceed
                and last_order_status.is_long
        ):
            macd_histogram, stock_rsi_d, stock_rsi_k = self._get_signals(candles)
            if (
                    (stock_rsi_k[-1] > stock_rsi_d[-1]
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
                    (stock_rsi_k[-1] < stock_rsi_d[-1]
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

        if last_order_status.ready_to_procceed and last_order_status.is_long:
            macd_histogram, stock_rsi_d, stock_rsi_k = self._get_signals(candles)
            is_profit, take_profit = self._is_take_profit(candles)
            is_loss, stop_loss = self._is_stop_loss(candles)
            if (
                    (macd_histogram[-1] >= 0 and macd_histogram[-1] < macd_histogram[-2] and stock_rsi_k[-1] < stock_rsi_d[-1])
                    or is_profit
                    or is_loss
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
        macd_data = macd(close, 12, 26)
        macd_histogram = macd_data["MACDh_12_26_9"]
        stoch_rsi_data = stochrsi(close)
        stock_rsi_k = stoch_rsi_data["STOCHRSIk_14_14_3_3"]
        stock_rsi_d = stoch_rsi_data["STOCHRSId_14_14_3_3"]
        return macd_histogram, stock_rsi_d, stock_rsi_k

    def _get_trend(self, candles):
        short_close_price = candles.close[-1]
        short_isa, short_isb = senkou_span_a_b(candles.high, candles.low)
        is_long = short_close_price > short_isa[-26] and short_close_price > short_isb[-26]
        is_short = short_close_price < short_isa[-26] and short_close_price < short_isb[-26]

        return is_long, is_short
