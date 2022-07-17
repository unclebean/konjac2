import logging
from pandas_ta.momentum import macd, stochrsi
from pandas_ta.overlap import ichimoku
from .abc_strategy import ABCStrategy
from ..indicator.utils import TradeType

log = logging.getLogger(__name__)


class MacdHistogramStrategy(ABCStrategy):
    strategy_name = "macd histogram strategy"

    def __init__(self, symbol: str):
        ABCStrategy.__init__(self, symbol)

    def seek_trend(self, candles, h4_candles):
        ichimoku_df, _ = ichimoku(candles.high, candles.low, candles.close)
        isa = ichimoku_df["ISA_9"]
        isb = ichimoku_df["ISB_26"]
        close_price = candles.close[-1]
        self._delete_last_in_progress_trade()
        if close_price > isa[-26] and close_price > isb[-26]:
            self._start_new_trade(TradeType.long.name, candles.index[-1])
        if close_price < isa[-26] and close_price < isb[-26]:
            self._start_new_trade(TradeType.short.name, candles.index[-1])

    def entry_signal(self, candles, h4_candles):
        last_order_status = self._can_open_new_trade()
        longer_timeframe_trend = self._get_longer_timeframe_volatility(candles, h4_candles)

        log.info(f"{self.symbol} heikin ashi trend {longer_timeframe_trend}")

        if (
                last_order_status.ready_to_procceed
                and last_order_status.is_long
                and longer_timeframe_trend == TradeType.long.name
        ):
            macd_data = macd(candles.close, 13, 34)
            macd_histogram = macd_data["MACDh_13_34_9"]
            stoch_rsi_data = stochrsi(candles.close)
            stock_rsi_k = stoch_rsi_data["STOCHRSIk_14_14_3_3"]
            stock_rsi_d = stoch_rsi_data["STOCHRSId_14_14_3_3"]
            if (
                    ((macd_histogram[-1] <= 0 or macd_histogram[-2] < 0 < macd_histogram[-1])
                     and macd_histogram[-2] <= macd_histogram[-1]
                     and stock_rsi_k[-1] > stock_rsi_d[-1]) or (
                    macd_histogram[-1] > 0 and stock_rsi_k[-1] > stock_rsi_d[-1] and stock_rsi_k[-2] <= stock_rsi_d[-2])
            ):
                return self._update_open_trade(
                    TradeType.long.name, candles.close[-1], "macd_ichimoku", macd_histogram[-1], candles.index[-1]
                )
        if (
                last_order_status.ready_to_procceed
                and last_order_status.is_short
                and longer_timeframe_trend == TradeType.short.name
        ):
            macd_data = macd(candles.close, 13, 34)
            macd_histogram = macd_data["MACDh_13_34_9"]
            stoch_rsi_data = stochrsi(candles.close)
            stock_rsi_k = stoch_rsi_data["STOCHRSIk_14_14_3_3"]
            stock_rsi_d = stoch_rsi_data["STOCHRSId_14_14_3_3"]
            if (
                    ((macd_histogram[-1] >= 0 or macd_histogram[-2] > 0 > macd_histogram[-1])
                     and macd_histogram[-2] >= macd_histogram[-1]
                     and stock_rsi_k[-1] < stock_rsi_d[-1]) or (
                    macd_histogram[-1] < 0 and stock_rsi_k[-1] < stock_rsi_d[-1] and stock_rsi_k[-2] >= stock_rsi_d[-2])
            ):
                return self._update_open_trade(
                    TradeType.short.name, candles.close[-1], "macd_ichimoku", macd_histogram[-1], candles.index[-1]
                )

        return False

    def exit_signal(self, candles, h4_candles):
        last_order_status = self._can_close_trade()

        if last_order_status.ready_to_procceed and last_order_status.is_long:
            macd_data = macd(candles.close, 13, 34)
            macd_histogram = macd_data["MACDh_13_34_9"]
            is_profit, take_profit = self._is_take_profit(candles)
            is_loss, stop_loss = self._is_stop_loss(candles)
            longer_timeframe_trend = self._get_longer_timeframe_volatility(candles, h4_candles)
            log.info(
                f"{self.symbol} is_profit {is_profit} take_profit {take_profit} is_loss {is_loss} stop_loss {stop_loss} trend {longer_timeframe_trend}"
            )
            if (
                    (macd_histogram[-1] >= 0 and macd_histogram[-1] < macd_histogram[-2])
                    or is_profit
                    or is_loss
                    or longer_timeframe_trend != TradeType.long.name
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
            macd_data = macd(candles.close, 13, 34)
            macd_histogram = macd_data["MACDh_13_34_9"]
            is_profit, take_profit = self._is_take_profit(candles)
            is_loss, stop_loss = self._is_stop_loss(candles)
            longer_timeframe_trend = self._get_longer_timeframe_volatility(candles, h4_candles)
            log.info(
                f"{self.symbol} is_profit {is_profit} take_profit {take_profit} is_loss {is_loss} stop_loss {stop_loss} trend {longer_timeframe_trend}"
            )
            if (
                    (macd_histogram[-1] <= 0 and macd_histogram[-1] > macd_histogram[-2])
                    or is_profit
                    or is_loss
                    or longer_timeframe_trend != TradeType.short.name
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
