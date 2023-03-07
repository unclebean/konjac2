from pandas_ta import adx, rsi, bbands

from konjac2.indicator.rsi_trend import rsi_trend
from konjac2.indicator.utils import TradeType
from konjac2.strategy.abc_strategy import ABCStrategy


class BBAdxRsiV2(ABCStrategy):
    strategy_name = "bb adx rsi v2"

    def __init__(self, symbol: str, trade_short_order=True, trade_long_order=True):
        ABCStrategy.__init__(self, symbol, trade_short_order, trade_long_order)

    def seek_trend(self, candles, day_candles=None):
        trend = rsi_trend(candles)
        rsi_data = rsi(candles.close, length=5)
        adx_ = adx(candles.high, candles.low, candles.close)
        adx_value = adx_['ADX_14'][-1]
        if (trend[-1] > 0 and adx_value < 30 and rsi_data[-2] <= 30 and rsi_data[-1] > 30) or (trend[-2] < 0 and trend[-1] > 0):
            self._delete_last_in_progress_trade()
            self._start_new_trade(TradeType.long.name, candles.index[-1], h4_date=day_candles.index[-1])
        if (trend[-1] < 0 and adx_value < 30 and rsi_data[-2] >= 70 and rsi_data[-1] < 70) or (trend[-2] > 0 and trend[-1] < 0):
            self._delete_last_in_progress_trade()
            self._start_new_trade(TradeType.short.name, candles.index[-1], h4_date=day_candles.index[-1])

    def entry_signal(self, candles, day_candles=None) -> bool:
        last_order_status = self._can_open_new_trade()
        bb_20 = bbands(candles.close, 20)
        bb_20_low = bb_20["BBL_20_2.0"]
        bb_20_up = bb_20["BBU_20_2.0"]
        rsi_data = rsi(candles.close, length=5)
        if (
                last_order_status.ready_to_procceed
                and last_order_status.is_long
                and bb_20_low[-2] >= candles.close[-2]
                and bb_20_low[-1] < candles.close[-1]
                and rsi_data[-1] > 30
        ):
            return self._update_open_trade(
                TradeType.long.name, candles.close[-1], self.strategy_name, 0, candles.index[-1]
            )
        if (
                last_order_status.ready_to_procceed
                and last_order_status.is_short
                and bb_20_up[-2] <= candles.close[-2]
                and bb_20_up[-1] > candles.close[-1]
                and rsi_data[-1] < 70
        ):
            return self._update_open_trade(
                TradeType.short.name, candles.close[-1], self.strategy_name, 0, candles.index[-1]
            )

    def exit_signal(self, candles, day_candles=None) -> bool:
        last_order_status = self._can_close_trade()
        rsi_data = rsi(candles.close, length=14)
        bb_20 = bbands(candles.close, 20)
        bb_20_low = bb_20["BBL_20_2.0"]
        bb_20_up = bb_20["BBU_20_2.0"]
        is_profit, take_profit = self._is_take_profit(candles)
        is_loss, stop_loss = self._is_stop_loss(candles)
        if last_order_status.ready_to_procceed \
                and last_order_status.is_long \
                and (is_profit or is_loss or bb_20_up[-1] <= candles.close[-1] or rsi_data[-1] >= 70):
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
                and (is_profit or is_loss or bb_20_low[-1] >= candles.close[-1] or rsi_data[-1] <= 30):
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
