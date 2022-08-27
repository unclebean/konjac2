from pandas_ta import willr

from konjac2.indicator.utils import TradeType
from konjac2.indicator.vwap import VWAP, RSI_VWAP
from konjac2.strategy.abc_strategy import ABCStrategy


class VwapRsiWillR(ABCStrategy):
    strategy_name = "vwap rsi willR"

    def seek_trend(self, candles, day_candles=None):
        r_vwap = RSI_VWAP(candles, delta_hours=0, group_by="week")
        if r_vwap[-2] <= 19 and r_vwap[-1] > 19:
            self._delete_last_in_progress_trade()
            self._start_new_trade(TradeType.long.name, candles.index[-1], h4_date=day_candles.index[-1])
        if r_vwap[-1] >= 80 or r_vwap[-1] <= 19:
            self._delete_last_in_progress_trade()

    def entry_signal(self, candles, day_candles=None) -> bool:
        willr_ = willr(candles.high, candles.low, candles.close)
        last_order_status = self._can_open_new_trade()
        vwap_, _, _ = VWAP(candles, delta_hours=0, group_by="week")
        if (
                last_order_status.ready_to_procceed
                and last_order_status.is_long
                and willr_[-2] <= -80 < willr_[-1]
        ):
            return self._update_open_trade(
                TradeType.long.name, candles.close[-1], self.strategy_name, 0, candles.index[-1]
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
