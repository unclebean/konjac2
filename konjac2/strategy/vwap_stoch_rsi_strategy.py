from pandas_ta import adx, rsi, bbands, hma, sma, stochrsi

from konjac2.indicator.utils import TradeType
from konjac2.indicator.vwap import VWAP
from konjac2.strategy.abc_strategy import ABCStrategy


class VwapStochRsi(ABCStrategy):
    strategy_name = "vwap stoch rsi"

    def __init__(self, symbol: str, trade_short_order=True):
        ABCStrategy.__init__(self, symbol, trade_short_order)

    def seek_trend(self, candles, day_candles=None):
        sma_500 = sma(candles.close, length=500)
        self._delete_last_in_progress_trade()
        if sma_500[-1] < candles.close[-1]:
            self._start_new_trade(TradeType.long.name, candles.index[-1], h4_date=day_candles.index[-1])
        if sma_500[-1] > candles.close[-1]:
            self._start_new_trade(TradeType.short.name, candles.index[-1], h4_date=day_candles.index[-1])

    def entry_signal(self, candles, day_candles=None) -> bool:
        last_order_status = self._can_open_new_trade()
        _, upper_bands, lower_bands = VWAP(candles)
        stoch_rsi_data = stochrsi(candles.close)
        stock_rsi_k = stoch_rsi_data["STOCHRSIk_14_14_3_3"]
        if (
                last_order_status.ready_to_procceed
                and last_order_status.is_long
                and lower_bands[-1] > candles.close[-1]
                and stock_rsi_k[-2] <= 30
                and stock_rsi_k[-1] > 30
        ):
            return self._update_open_trade(
                TradeType.long.name, candles.close[-1], self.strategy_name, 0, candles.index[-1]
            )
        if (
                last_order_status.ready_to_procceed
                and last_order_status.is_short
                and lower_bands[-1] < candles.close[-1]
                and stock_rsi_k[-2] >= 70
                and stock_rsi_k[-1] < 70
        ):
            return self._update_open_trade(
                TradeType.short.name, candles.close[-1], self.strategy_name, 0, candles.index[-1]
            )

    def exit_signal(self, candles, day_candles=None) -> bool:
        last_order_status = self._can_close_trade()
        _, upper_bands, lower_bands = VWAP(candles)
        stoch_rsi_data = stochrsi(candles.close)
        stock_rsi_k = stoch_rsi_data["STOCHRSIk_14_14_3_3"]
        is_profit, take_profit = self._is_take_profit(candles)
        is_loss, stop_loss = self._is_stop_loss(candles)
        if last_order_status.ready_to_procceed \
                and last_order_status.is_long \
                and (is_profit or is_loss or stock_rsi_k[-1] > 70):
            return self._update_close_trade(
                TradeType.short.name,
                candles.close[-1],
                self.strategy_name,
                candles.close[-1],
                candles.index[-1],
                is_profit,
                is_loss,
                take_profit,
                stop_loss,
            )

        if last_order_status.ready_to_procceed \
                and last_order_status.is_short \
                and (is_profit or is_loss or stock_rsi_k[-1] < 30):
            return self._update_close_trade(
                TradeType.long.name,
                candles.close[-1],
                self.strategy_name,
                candles.close[-1],
                candles.index[-1],
                is_profit,
                is_loss,
                take_profit,
                stop_loss,
            )
