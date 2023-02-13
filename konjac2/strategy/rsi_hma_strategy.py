from pandas_ta import adx, rsi, bbands, hma

from konjac2.indicator.utils import TradeType
from konjac2.strategy.abc_strategy import ABCStrategy


class RsiHma(ABCStrategy):
    strategy_name = "rsi"

    def __init__(self, symbol: str, trade_short_order=True):
        ABCStrategy.__init__(self, symbol, trade_short_order)

    def seek_trend(self, candles, day_candles=None):
        rsi_data = rsi(candles.close, length=5)
        self._delete_last_in_progress_trade()
        if rsi_data[-1] >= 50:
            self._start_new_trade(TradeType.long.name, candles.index[-1], h4_date=day_candles.index[-1])
        if rsi_data[-1] >= 50:
            self._start_new_trade(TradeType.short.name, candles.index[-1], h4_date=day_candles.index[-1])

    def entry_signal(self, candles, day_candles=None) -> bool:
        last_order_status = self._can_open_new_trade()
        hma_data = hma(candles.close, length=100)
        if (
                last_order_status.ready_to_procceed
                and last_order_status.is_long
                and hma_data[-2] > candles.close[-2]
                and hma_data[-1] < candles.close[-1]
        ):
            return self._update_open_trade(
                TradeType.long.name, candles.close[-1], self.strategy_name, 0, candles.index[-1]
            )
        if (
                last_order_status.ready_to_procceed
                and last_order_status.is_short
                and hma_data[-2] < candles.close[-2]
                and hma_data[-1] > candles.close[-1]
        ):
            return self._update_open_trade(
                TradeType.short.name, candles.close[-1], self.strategy_name, 0, candles.index[-1]
            )

    def exit_signal(self, candles, day_candles=None) -> bool:
        last_order_status = self._can_close_trade()
        rsi_data = rsi(candles.close, length=5)
        hma_data = hma(candles.close, length=200)
        is_profit, take_profit = self._is_take_profit(candles)
        is_loss, stop_loss = self._is_stop_loss(candles)
        if last_order_status.ready_to_procceed \
                and last_order_status.is_long \
                and (is_profit or is_loss or rsi_data[-1] > 85 or hma_data[-1] > candles.close[-1]):
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
                and (is_profit or is_loss or rsi_data[-1] < 20 or hma_data[-1] < candles.close[-1]):
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
