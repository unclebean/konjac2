from pandas_ta import stoch, rsi, sma, macd

from konjac2.indicator.utils import TradeType
from konjac2.strategy.abc_strategy import ABCStrategy


class RSIStochMacdStrategy(ABCStrategy):
    strategy_name = "rsi stoch macd"

    def seek_trend(self, candles, day_candles=None):
        stoch_data = stoch(candles.high, candles.low, candles.close)
        stoch_k = stoch_data["STOCHk_14_3_3"]
        stoch_d = stoch_data["STOCHd_14_3_3"]
        if candles.index[-1].hour < 8 or candles.index[-1].hour > 22:
            return
        if (stoch_d[-2] < 20) and stoch_k[-1] > 20 and stoch_d[-1] > 20:
            self._delete_last_in_progress_trade()
            self._start_new_trade(TradeType.long.name, candles.index[-1], h4_date=day_candles.index[-1])
        if (stoch_d[-2] > 80) and stoch_k[-1] < 80 and stoch_d[-1] < 80:
            self._delete_last_in_progress_trade()
            self._start_new_trade(TradeType.short.name, candles.index[-1], h4_date=day_candles.index[-1])

    def entry_signal(self, candles, day_candles=None) -> bool:
        last_order_status = self._can_open_new_trade()
        is_long, is_short = self._get_signal(candles)
        if (
                last_order_status.ready_to_procceed
                and last_order_status.is_long
                and is_long
        ):
            return self._update_open_trade(
                TradeType.long.name, candles.close[-1], self.strategy_name, 0, candles.index[-1]
            )
        if (
                last_order_status.ready_to_procceed
                and last_order_status.is_short
                and is_short
        ):
            return self._update_open_trade(
                TradeType.short.name, candles.close[-1], self.strategy_name, 0, candles.index[-1]
            )

    def exit_signal(self, candles, day_candles=None) -> bool:
        last_order_status = self._can_close_trade()
        is_profit, take_profit = self._is_take_profit(candles)
        is_loss, stop_loss = self._is_stop_loss(candles)
        is_long, is_short = self._get_signal(candles)
        if last_order_status.ready_to_procceed \
                and last_order_status.is_long \
                and (is_profit or is_loss or not is_long):
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
                and (is_profit or is_loss or not is_short):
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

    def _get_signal(self, candles):
        stoch_data = stoch(candles.high, candles.low, candles.close)
        stoch_k = stoch_data["STOCHk_14_3_3"]
        stoch_d = stoch_data["STOCHd_14_3_3"]
        rsi_data = rsi(candles.close, length=14)
        rsi_sma_data = sma(rsi_data, length=14)
        macd_data = macd(candles.close)
        macd_ = macd_data["MACD_12_26_9"]
        macd_signal = macd_data["MACDs_12_26_9"]

        is_long = stoch_k[-1] > stoch_d[-1] and rsi_data[-1] > 50 and macd_[-1] > macd_signal[-1]
        is_short = stoch_k[-1] < stoch_d[-1] and rsi_data[-1] < 50 and macd_[-1] < macd_signal[-1]
        return is_long, is_short
