from pandas_ta import adx, rsi

from konjac2.indicator.utils import TradeType
from konjac2.strategy.abc_strategy import ABCStrategy


class TripleRsiAdxStrategy(ABCStrategy):
    strategy_name = "tripe rsi adx"

    def seek_trend(self, candles, day_candles=None):
        rsi7 = rsi(candles.close, length=7)
        rsi14 = rsi(candles.close, length=14)
        rsi21 = rsi(candles.close, length=21)
        if rsi7[-1] > rsi14[-1] > rsi21[-1] >= 50:
            self._delete_last_in_progress_trade()
            self._start_new_trade(TradeType.long.name, candles.index[-1], h4_date=day_candles.index[-1])
        if rsi7[-1] < rsi14[-1] < rsi21[-1] <= 50:
            self._delete_last_in_progress_trade()
            self._start_new_trade(TradeType.short.name, candles.index[-1], h4_date=day_candles.index[-1])

    def entry_signal(self, candles, day_candles=None) -> bool:
        last_order_status = self._can_open_new_trade()
        adx_ = adx(candles.high, candles.low, candles.close)
        adx_value = adx_['ADX_14']
        if (
                last_order_status.ready_to_procceed
                and last_order_status.is_long
                and adx_value[-1] > 20
                and adx_value[-3] < adx_value[-2] < adx_value[-1]
        ):
            return self._update_open_trade(
                TradeType.long.name, candles.close[-1], self.strategy_name, 0, candles.index[-1]
            )
        if (
                last_order_status.ready_to_procceed
                and last_order_status.is_short
                and adx_value[-1] > 20
                and adx_value[-3] < adx_value[-2] < adx_value[-1]
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
                and (is_profit or is_loss):
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
                and (is_profit or is_loss):
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
