from pandas_ta import stoch, psar

from konjac2.indicator.hurst import get_hurst_exponent
from konjac2.indicator.utils import TradeType
from konjac2.strategy.abc_strategy import ABCStrategy


class StochSarStrategy(ABCStrategy):
    strategy_name = "stoch sar"

    def seek_trend(self, candles, day_candles=None):
        stoch_data = stoch(candles.high, candles.low, candles.close, k=5, d=5, smooth_k=5)
        stoch_k = stoch_data["STOCHk_5_5_5"]
        stoch_d = stoch_data["STOCHd_5_5_5"]
        psar_ = psar(candles.high, candles.low, candles.close)
        last_psar = psar_['PSARl_0.02_0.2'][-1]
        trend = self._get_ris_vwap_trend(candles)
        hurst_result = get_hurst_exponent(candles.close.values)
        if stoch_k[-1] > stoch_d[-1] \
                and candles.close[-1] > last_psar \
                and trend is TradeType.long.name \
                and hurst_result > 0.5:
            self._delete_last_in_progress_trade()
            self._start_new_trade(TradeType.long.name, candles.index[-1], h4_date=day_candles.index[-1])
        if stoch_k[-1] < stoch_d[-1] \
                and candles.close[-1] < last_psar \
                and trend is TradeType.short.name \
                and hurst_result > 0.5:
            self._delete_last_in_progress_trade()
            self._start_new_trade(TradeType.short.name, candles.index[-1], h4_date=day_candles.index[-1])

    def entry_signal(self, candles, day_candles=None) -> bool:
        last_order_status = self._can_open_new_trade()
        psar_ = psar(candles.high, candles.low, candles.close)['PSARl_0.02_0.2']
        if (
                last_order_status.ready_to_procceed
                and last_order_status.is_long
                and candles.close[-3] > psar_[-3]
                and candles.close[-2] > psar_[-2]
                and candles.close[-1] > psar_[-1]
                and not (candles.close[-3] < candles.open[-3]
                         and candles.close[-2] < candles.open[-2]
                         and candles.close[-1] < candles.open[-1])
        ):
            return self._update_open_trade(
                TradeType.long.name, candles.close[-1], self.strategy_name, 0, candles.index[-1]
            )
        if (
                last_order_status.ready_to_procceed
                and last_order_status.is_short
                and candles.close[-3] < psar_[-3]
                and candles.close[-2] < psar_[-2]
                and candles.close[-1] < psar_[-1]
                and not (candles.close[-3] > candles.open[-3]
                         and candles.close[-2] > candles.open[-2]
                         and candles.close[-1] > candles.open[-1])
        ):
            return self._update_open_trade(
                TradeType.short.name, candles.close[-1], self.strategy_name, 0, candles.index[-1]
            )

    def exit_signal(self, candles, day_candles=None) -> bool:
        last_order_status = self._can_close_trade()
        is_profit, take_profit = self._is_take_profit(candles)
        is_loss, stop_loss = self._is_stop_loss(candles)
        stoch_data = stoch(candles.high, candles.low, candles.close, k=5, d=5, smooth_k=5)
        stoch_k = stoch_data["STOCHk_5_5_5"]
        stoch_d = stoch_data["STOCHd_5_5_5"]
        psar_ = psar(candles.high, candles.low, candles.close)
        last_psar = psar_['PSARl_0.02_0.2'][-1]
        hurst_result = get_hurst_exponent(candles.close.values)
        if last_order_status.ready_to_procceed \
                and last_order_status.is_long \
                and (hurst_result < 0.5 or is_profit or is_loss or (stoch_k[-1] < stoch_d[-1] and candles.close[-1] < last_psar)):
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
                and (hurst_result < 0.5 or is_profit or is_loss or (stoch_k[-1] > stoch_d[-1] and candles.close[-1] > last_psar)):
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
