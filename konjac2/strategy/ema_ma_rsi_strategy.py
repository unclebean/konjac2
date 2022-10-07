from pandas_ta import rsi, ema

from konjac2.indicator.moving_average import moving_average
from konjac2.indicator.utils import TradeType
from konjac2.strategy.abc_strategy import ABCStrategy


class EmaMaRsiStrategy(ABCStrategy):
    strategy_name = "ema ma cross strategy"

    def seek_trend(self, candles, day_candles=None):
        rsi_data = rsi(candles.close, length=14)
        self._delete_last_in_progress_trade()
        if rsi_data[-1] > 50:
            self._start_new_trade(TradeType.long.name, candles.index[-1], h4_date=day_candles.index[-1])
        if rsi_data[-1] < 50:
            self._start_new_trade(TradeType.short.name, candles.index[-1], h4_date=day_candles.index[-1])

    def entry_signal(self, candles, day_candles=None) -> bool:
        last_order_status = self._can_open_new_trade()
        low_price = candles.low[-1]
        high_price = candles.high[-1]
        ema_10 = ema(candles.close, 10)
        ma_10 = moving_average(candles.close, 10)
        if (
                last_order_status.ready_to_procceed
                and last_order_status.is_long
                and ema_10[-2] >= ma_10[-2]
                and ema_10[-1] < ma_10[-1] < low_price
        ):
            return self._update_open_trade(
                TradeType.long.name, candles.close[-1], self.strategy_name, 0, candles.index[-1]
            )
        if (
                last_order_status.ready_to_procceed
                and last_order_status.is_short
                and ema_10[-2] <= ma_10[-2]
                and ema_10[-1] > ma_10[-1] > high_price
        ):
            return self._update_open_trade(
                TradeType.short.name, candles.close[-1], self.strategy_name, 0, candles.index[-1]
            )

    def exit_signal(self, candles, day_candles=None) -> bool:
        last_order_status = self._can_close_trade()
        is_profit, take_profit = self._is_take_profit(candles)
        is_loss, stop_loss = self._is_stop_loss(candles)
        if last_order_status.ready_to_procceed \
                and last_order_status.is_long \
                and (is_profit):
            return self._update_close_trade(
                TradeType.short.name,
                candles.close[-1],
                self.strategy_name,
                candles.close[-1],
                candles.index[-1],
                is_profit,
                False,
                take_profit,
                stop_loss,
            )

        if last_order_status.ready_to_procceed \
                and last_order_status.is_short \
                and (is_profit):
            return self._update_close_trade(
                TradeType.long.name,
                candles.close[-1],
                self.strategy_name,
                candles.close[-1],
                candles.index[-1],
                is_profit,
                False,
                take_profit,
                stop_loss,
            )
