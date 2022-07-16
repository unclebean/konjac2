import logging
from pandas_ta.momentum import stochrsi
from pandas_ta.overlap import ema
from .abc_strategy import ABCStrategy
from ..indicator.utils import TradeType

log = logging.getLogger(__name__)


class EmaStochRsiStrategy(ABCStrategy):
    strategy_name = "ema stoch_rsi strategy"

    def __init__(self, symbol: str):
        ABCStrategy.__init__(self, symbol)

    def seek_trend(self, candles, h4_candles):
        ema_8 = ema(candles.close, 8)
        ema_14 = ema(candles.close, 14)
        ema_50 = ema(candles.close, 50)
        close_price = candles.close[-1]
        self._delete_last_in_progress_trade()
        if ema_8[-1] < close_price and ema_14[-1] < close_price and ema_50[-1] < close_price:
            self._start_new_trade(TradeType.long.name, candles.index[-1])
        if ema_8[-1] > close_price and ema_14[-1] > close_price and ema_50[-1] > close_price:
            self._start_new_trade(TradeType.short.name, candles.index[-1])

    def entry_signal(self, candles, h4_candles):
        last_order_status = self._can_open_new_trade()
        longer_timeframe_trend = self._get_longer_timeframe_volatility(candles, h4_candles)
        if (
                last_order_status.ready_to_procceed
                and last_order_status.is_long
        ):
            stoch_rsi_data = stochrsi(candles.close)
            stock_rsi_k = stoch_rsi_data["STOCHRSIk_14_14_3_3"]
            stock_rsi_d = stoch_rsi_data["STOCHRSId_14_14_3_3"]
            if (
                    stock_rsi_k[-1] > stock_rsi_d[-1]
                    and stock_rsi_k[-2] <= stock_rsi_d[-2]
                    and longer_timeframe_trend == TradeType.long.name
            ):
                return self._update_open_trade(
                    TradeType.long.name, candles.close[-1], "eam_stoch_rsi", stock_rsi_k[-1], candles.index[-1]
                )
        if (
                last_order_status.ready_to_procceed
                and last_order_status.is_short
        ):
            stoch_rsi_data = stochrsi(candles.close)
            stock_rsi_k = stoch_rsi_data["STOCHRSIk_14_14_3_3"]
            stock_rsi_d = stoch_rsi_data["STOCHRSId_14_14_3_3"]
            if (
                    stock_rsi_k[-1] < stock_rsi_d[-1]
                    and stock_rsi_k[-2] >= stock_rsi_d[-2]
                    and longer_timeframe_trend == TradeType.short.name
            ):
                return self._update_open_trade(
                    TradeType.short.name, candles.close[-1], "eam_stoch_rsi", stock_rsi_k[-1], candles.index[-1]
                )

        return False

    def exit_signal(self, candles, h4_candles):
        last_order_status = self._can_close_trade()
        stoch_rsi_data = stochrsi(candles.close)
        stock_rsi_k = stoch_rsi_data["STOCHRSIk_14_14_3_3"]
        stock_rsi_d = stoch_rsi_data["STOCHRSId_14_14_3_3"]
        ema_8 = ema(candles.close, 8)
        ema_14 = ema(candles.close, 14)
        ema_50 = ema(candles.close, 50)
        close_price = candles.close[-1]
        longer_timeframe_trend = self._get_longer_timeframe_volatility(candles, h4_candles)

        if last_order_status.ready_to_procceed and last_order_status.is_long:
            is_profit, take_profit = self._is_take_profit(candles)
            is_loss, stop_loss = self._is_stop_loss(candles)
            if (
                stock_rsi_k[-1] < stock_rsi_d[-1]
                or ema_8[-1] > close_price
                or ema_14[-1] > close_price
                or ema_50[-1] > close_price
                or is_profit
                or is_loss
                or longer_timeframe_trend is not TradeType.long.name
            ):
                return self._update_close_trade(
                    TradeType.short.name,
                    candles.close[-1],
                    "ema_stoch_rsi",
                    0,
                    candles.index[-1],
                    is_profit,
                    is_loss,
                    take_profit,
                    stop_loss,
                )
        if last_order_status.ready_to_procceed and last_order_status.is_short:
            is_profit, take_profit = self._is_take_profit(candles)
            is_loss, stop_loss = self._is_stop_loss(candles)
            if (
                stock_rsi_k[-1] > stock_rsi_d[-1]
                or ema_8[-1] < close_price
                or ema_14[-1] < close_price
                or ema_50[-1] < close_price
                or is_profit
                or is_loss
                or longer_timeframe_trend is not TradeType.short.name
            ):
                return self._update_close_trade(
                    TradeType.long.name,
                    candles.close[-1],
                    "ema_stoch_rsi",
                    0,
                    candles.index[-1],
                    is_profit,
                    is_loss,
                    take_profit,
                    stop_loss,
                )
        return False
