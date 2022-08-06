import logging

from pandas_ta import ichimoku
from pandas_ta.momentum import macd
from .abc_strategy import ABCStrategy
from ..indicator.utils import TradeType

log = logging.getLogger(__name__)


class MacdRsiVwapStrategy(ABCStrategy):
    strategy_name = "macd rsi vwap"

    def __init__(self, symbol: str):
        ABCStrategy.__init__(self, symbol)

    def seek_trend(self, candles, day_candles=None):
        ichimoku_df, _ = ichimoku(candles.high, candles.low, candles.close)
        isa = ichimoku_df["ISA_9"]
        isb = ichimoku_df["ISB_26"]
        close_price = candles.close[-1]
        self._delete_last_in_progress_trade()

        if close_price > isa[-26] and close_price > isb[-26]:
            self._start_new_trade(TradeType.long.name, candles.index[-1], open_type="ichimoku",
                                  h4_date=day_candles.index[-1])
            return
        if close_price < isa[-26] and close_price < isb[-26]:
            self._start_new_trade(TradeType.short.name, candles.index[-1], open_type="ichimoku",
                                  h4_date=day_candles.index[-1])

    def entry_signal(self, candles, day_candles=None):
        last_order_status = self._can_open_new_trade()
        macd_data = macd(candles.close, 13, 34)
        macd_ = macd_data["MACD_13_34_9"]
        macd_signal = macd_data["MACDs_13_34_9"]
        longer_timeframe_trend = self._get_longer_timeframe_volatility(candles, day_candles)

        if last_order_status.ready_to_procceed \
                and last_order_status.is_long \
                and macd_[-1] > macd_signal[-1] \
                and macd_[-2] <= macd_signal[-2] \
                and longer_timeframe_trend == TradeType.long.name:
            return self._update_open_trade(
                TradeType.long.name, candles.close[-1], "macd_vwap", macd_[-1], candles.index[-1]
            )
        if last_order_status.ready_to_procceed \
                and last_order_status.is_short \
                and macd_[-1] < macd_signal[-1] \
                and macd_[-2] >= macd_signal[-2] \
                and longer_timeframe_trend == TradeType.short.name:
            return self._update_open_trade(
                TradeType.short.name, candles.close[-1], "macd_vwap", macd_[-1], candles.index[-1]
            )

        return False

    def exit_signal(self, candles, day_candles=None):
        last_order_status = self._can_close_trade()
        macd_data = macd(candles.close, 13, 34)
        macd_ = macd_data["MACD_13_34_9"]
        macd_hist = macd_data["MACDh_13_34_9"]
        is_profit, take_profit = self._is_take_profit(candles)
        is_loss, stop_loss = self._is_stop_loss(candles)

        if last_order_status.ready_to_procceed and last_order_status.is_long \
                and (
                macd_hist[-1] < macd_hist[-2]
                or is_profit
                or is_loss
        ):
            return self._update_close_trade(
                TradeType.short.name,
                candles.close[-1],
                "macd_vwap",
                macd_[-1],
                candles.index[-1],
                is_profit,
                is_loss,
                take_profit,
                stop_loss,
            )
        if last_order_status.ready_to_procceed and last_order_status.is_short \
                and (
                macd_hist[-1] > macd_hist[-2]
                or is_profit
                or is_loss
        ):
            return self._update_close_trade(
                TradeType.long.name,
                candles.close[-1],
                "macd_vwap",
                macd_[-1],
                candles.index[-1],
                is_profit,
                is_loss,
                take_profit,
                stop_loss,
            )
        return False
