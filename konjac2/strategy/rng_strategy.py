from datetime import timedelta

from konjac2.indicator.range_filter import range_filter
from konjac2.indicator.utils import TradeType
from konjac2.models.trade import get_last_time_trade
from konjac2.strategy.abc_strategy import ABCStrategy


class RNGStrategy(ABCStrategy):
    strategy_name = "rng strategy"

    def seek_trend(self, candles, day_candles=None):
        is_long, is_short = self._get_signals(candles)
        self._delete_last_in_progress_trade()
        if is_long:
            self._start_new_trade(TradeType.long.name, candles.index[-1], h4_date=day_candles.index[-1])
        if is_short:
            self._start_new_trade(TradeType.short.name, candles.index[-1], h4_date=day_candles.index[-1])

    def entry_signal(self, candles, day_candles=None) -> bool:
        last_order_status = self._can_open_new_trade()
        if (
                last_order_status.ready_to_procceed
                and last_order_status.is_long
        ):
            return self._update_open_trade(
                TradeType.long.name, candles.close[-1], self.strategy_name, 0, candles.index[-1]
            )
        if (
                last_order_status.ready_to_procceed
                and last_order_status.is_short
        ):
            return self._update_open_trade(
                TradeType.short.name, candles.close[-1], self.strategy_name, 0, candles.index[-1]
            )

    def exit_signal(self, candles, day_candles=None) -> bool:
        last_order_status = self._can_close_trade()
        if last_order_status.ready_to_procceed is False:
            return False
        last_trade = get_last_time_trade(self.symbol)
        open_date = last_trade.entry_date + timedelta(hours=1)
        is_long, is_short = self._get_signals(candles)
        is_profit, take_profit = self._is_take_profit(candles)
        is_loss, stop_loss = self._is_stop_loss(candles)
        if last_order_status.ready_to_procceed \
                and last_order_status.is_long \
                and (is_loss or is_profit or open_date == candles.index[-1]):
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
                and (is_loss or is_profit or open_date == candles.index[-1]):
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

    def _get_signals(self, candles):
        close_price = candles.close
        rng_filter, upper, lower = range_filter(close_price)
        is_long = close_price[-1] < rng_filter[-1] and upper[-1] < 0
        is_short = close_price[-1] > rng_filter[-1] and lower[-1] < 0

        return is_long, is_short
