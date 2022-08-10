import numpy
from pandas_ta import macd, rsi, stoch, sma

from konjac2.indicator.utils import TradeType
from konjac2.strategy.abc_strategy import ABCStrategy


class StrategyFive(ABCStrategy):
    def seek_trend(self, candles, day_candles=None):
        if self._get_indicators(candles):
            self._delete_last_in_progress_trade()
            self._start_new_trade(TradeType.long.name, candles.index[-1])

    def entry_signal(self, candles, day_candles=None) -> bool:
        last_order_status = self._can_open_new_trade()

        if (
                last_order_status.ready_to_procceed
                and last_order_status.is_long
        ):
            return self._update_open_trade(
                TradeType.long.name, candles.close[-1], "strategy 5", 0, candles.index[-1]
            )

    def exit_signal(self, candles, day_candles=None) -> bool:
        last_order_status = self._can_close_trade()
        is_profit, take_profit = self._is_take_profit(candles)
        is_loss, stop_loss = self._is_stop_loss(candles)
        rsi_data = rsi(candles.close)
        macd_data = macd(candles.close, 12, 26)
        macd_ = macd_data["MACD_12_26_9"]
        macd_signal = macd_data["MACDs_12_26_9"]
        if last_order_status.ready_to_procceed \
                and last_order_status.is_long \
                and (macd_[-1] < 0 or (abs(macd_[-1] - macd_signal[-1]) > 4) or rsi_data[-1] > 70):
            return self._update_close_trade(
                TradeType.short.name,
                candles.close[-1],
                "strategy 5",
                candles.close[-1],
                candles.index[-1],
                False,
                False,
                take_profit,
                stop_loss,
            )

    def _get_indicators(self, candles):
        rsi_data = rsi(candles.close)
        rsi_ = 0.1 * (rsi_data - 50)
        fisher_rsi = (numpy.exp(2 * rsi_) - 1) / (numpy.exp(2 * rsi_) + 1)
        fisher_rsi_norma = 50 * (fisher_rsi + 1)
        stoch_data = stoch(candles.high, candles.low, candles.close)
        stoch_k = stoch_data["STOCHk_14_3_3"]
        stoch_d = stoch_data["STOCHd_14_3_3"]
        volume_volatility = candles.volume.rolling(150).mean() * 4
        sma_ = sma(candles.close, 40)
        # print(f"{candles.close[-1]} < {sma_[-1]} and {stoch_d[-1]} < {stoch_k[-1]} and {rsi_[-1]} > 1 and {stoch_d[-1]} > 26 and {fisher_rsi_norma[-1]} < 70")

        return candles.volume[-1] > volume_volatility[-1] \
               and candles.close[-1] < sma_[-1] \
               and stoch_d[-1] > stoch_k[-1] \
               and stoch_d[-1] > 1 and fisher_rsi_norma[-1] < 10 and rsi_data[-1] > 26
