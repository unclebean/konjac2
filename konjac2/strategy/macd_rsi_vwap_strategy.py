import logging
from pandas_ta.momentum import macd
from .abc_strategy import ABCStrategy
from ..indicator.squeeze_momentum import is_squeeze
from ..indicator.utils import TradeType

log = logging.getLogger(__name__)


class MacdRsiVwapStrategy(ABCStrategy):
    strategy_name = "macd rsi vwap"

    def __init__(self, symbol: str):
        ABCStrategy.__init__(self, symbol)

    def seek_trend(self, candles, day_candles=None):
        longer_timeframe_trend = self._get_ris_vwap_rend(candles)
        self._delete_last_in_progress_trade()

        if longer_timeframe_trend is not None:
            self._start_new_trade(longer_timeframe_trend, candles.index[-1], open_type="squeeze",
                                  h4_date=day_candles.index[-1])
            log.info(f"{self.symbol} in progress with no squeeze!")

    def entry_signal(self, candles, day_candles=None):
        last_order_status = self._can_open_new_trade()
        longer_timeframe_trend = self._get_ris_vwap_rend(candles)
        macd_data = macd(candles.close, 12, 26)
        macd_ = macd_data["MACD_12_26_9"]
        macd_signal = macd_data["MACDs_12_26_9"]
        is_sqz = is_squeeze(candles)

        if last_order_status.ready_to_procceed \
                and last_order_status.is_long \
                and longer_timeframe_trend == TradeType.long.name \
                and macd_[-1] > macd_signal[-1] \
                and macd_[-2] <= macd_signal[-2] \
                and not is_sqz:
            return self._update_open_trade(
                TradeType.long.name, candles.close[-1], "macd_vwap", macd_[-1], candles.index[-1]
            )
        if last_order_status.ready_to_procceed \
                and last_order_status.is_short \
                and longer_timeframe_trend == TradeType.short.name \
                and macd_[-1] < macd_signal[-1] \
                and macd_[-2] >= macd_signal[-2] \
                and not is_sqz:
            return self._update_open_trade(
                TradeType.short.name, candles.close[-1], "macd_vwap", macd_[-1], candles.index[-1]
            )

        return False

    def exit_signal(self, candles, day_candles=None):
        last_order_status = self._can_close_trade()
        longer_timeframe_trend = self._get_ris_vwap_rend(candles)
        macd_data = macd(candles.close, 12, 26)
        macd_ = macd_data["MACD_12_26_9"]
        macd_hist = macd_data["MACDh_12_26_9"]
        is_profit, take_profit = self._is_take_profit(candles)
        is_loss, stop_loss = self._is_stop_loss(candles)

        if last_order_status.ready_to_procceed and last_order_status.is_long \
                and (
                macd_hist[-1] <= 0
                or is_profit
                or is_loss
                or longer_timeframe_trend != TradeType.long.name
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
                macd_hist[-1] >= 0
                or is_profit
                or is_loss
                or longer_timeframe_trend != TradeType.short.name
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
