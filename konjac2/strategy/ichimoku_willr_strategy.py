from pandas_ta import ichimoku, willr

from konjac2.indicator.senkou_span import senkou_span_a_b
from konjac2.indicator.utils import TradeType
from konjac2.strategy.abc_strategy import ABCStrategy


class IchimokuWillR(ABCStrategy):
    strategy_name = "ichimoku willR"

    def seek_trend(self, candles, day_candles=None):
        is_long, is_short = self._get_signals(candles, day_candles)
        trend = self._get_rsi_vwap_trend(candles)
        self._delete_last_in_progress_trade()
        if is_long and trend is TradeType.long.name:
            self._start_new_trade(TradeType.long.name, candles.index[-1], h4_date=day_candles.index[-1])
        if is_short and trend is TradeType.short.name:
            self._start_new_trade(TradeType.short.name, candles.index[-1], h4_date=day_candles.index[-1])

    def entry_signal(self, candles, day_candles=None) -> bool:
        last_order_status = self._can_open_new_trade()
        willr_ = willr(candles.high, candles.low, candles.close)
        if (
                last_order_status.ready_to_procceed
                and last_order_status.is_long
                and willr_[-2] <= -80 < willr_[-1] < -30
        ):
            return self._update_open_trade(
                TradeType.long.name, candles.close[-1], self.strategy_name, 0, candles.index[-1]
            )
        if (
                last_order_status.ready_to_procceed
                and last_order_status.is_short
                and willr_[-2] >= -20 > willr_[-1] > -70
        ):
            return self._update_open_trade(
                TradeType.short.name, candles.close[-1], self.strategy_name, 0, candles.index[-1]
            )

    def exit_signal(self, candles, day_candles=None) -> bool:
        last_order_status = self._can_close_trade()
        willr_ = willr(candles.high, candles.low, candles.close)
        is_profit, take_profit = self._is_take_profit(candles)
        is_loss, stop_loss = self._is_stop_loss(candles)
        if last_order_status.ready_to_procceed \
                and last_order_status.is_long \
                and (willr_[-1] >= -30 or is_profit or is_loss):
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
                and (willr_[-1] <= -70 or is_profit or is_loss):
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

    def _get_signals(self, candles, day_candles):
        short_close_price = candles.close[-1]
        long_close_price = day_candles.close[-1]
        short_isa, short_isb = self._get_ichimoku(candles)
        long_isa, long_isb = self._get_ichimoku(day_candles)
        is_long = short_close_price > short_isa[-26] and short_close_price > short_isb[-26] \
               and long_close_price > long_isa[-26] and long_close_price > long_isb[-26]
        is_short = short_close_price < short_isa[-26] and short_close_price < short_isb[-26] \
               and long_close_price < long_isa[-26] and long_close_price < long_isb[-26]

        return is_long, is_short

    def _get_ichimoku(self, candles):
        '''
        ichimoku_, _ = ichimoku(candles.high, candles.low, candles.close)
        isa = ichimoku_["ISA_9"]
        isb = ichimoku_["ISB_26"]
        '''
        isa, isb = senkou_span_a_b(candles.high, candles.low)

        return isa, isb
