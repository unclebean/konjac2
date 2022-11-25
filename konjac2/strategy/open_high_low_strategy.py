from konjac2.indicator.senkou_span import senkou_span_a_b
from konjac2.indicator.utils import TradeType
from konjac2.strategy.abc_strategy import ABCStrategy


class OpenHighLowStrategy(ABCStrategy):
    strategy_name = "open high low"

    def seek_trend(self, candles, day_candles=None):
        open_price = candles.open
        close_price = candles.close
        self._delete_last_in_progress_trade()
        if open_price[-3] < close_price[-3] and open_price[-2] < close_price[-2] and open_price[-1] < close_price[-1]:
            self._start_new_trade(TradeType.short.name, candles.index[-1], h4_date=day_candles.index[-1])
        if open_price[-3] > close_price[-3] and open_price[-2] > close_price[-2] and open_price[-1] > close_price[-1]:
            self._start_new_trade(TradeType.long.name, candles.index[-1], h4_date=day_candles.index[-1])

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
        is_profit, take_profit = self._is_take_profit(candles)
        is_loss, stop_loss = self._is_stop_loss(candles)
        open_price = candles.open
        close_price = candles.close
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

    def _get_signals(self, candles):
        short_isa, short_isb = senkou_span_a_b(candles.high, candles.low)
        short_close_price = candles.close[-1]
        is_long = short_close_price > short_isa[-26] and short_close_price > short_isb[-26]
        is_short = short_close_price < short_isa[-26] and short_close_price < short_isb[-26]

        return is_long, is_short
