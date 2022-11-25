from datetime import timedelta

from pandas_ta import supertrend

from konjac2.indicator.ut_bot import ut_bot
from konjac2.indicator.utils import TradeType
from konjac2.strategy.abc_strategy import ABCStrategy


class UTSuperTrendStrategy(ABCStrategy):
    strategy_name = "ut super trend"

    def seek_trend(self, candles, day_candles=None):
        pd_data = ut_bot(candles)
        if pd_data['Buy'].iat[-1]:
            self._delete_last_in_progress_trade()
            self._start_new_trade(TradeType.long.name, candles.index[-1], h4_date=day_candles.index[-1])
        if pd_data['Sell'].iat[-1]:
            self._delete_last_in_progress_trade()
            self._start_new_trade(TradeType.short.name, candles.index[-1], h4_date=day_candles.index[-1])

    def entry_signal(self, candles, day_candles=None) -> bool:
        last_order_status = self._can_open_new_trade()
        close_price = candles.close[-1]
        prev_close_price = candles.close[-2]
        super_trend = supertrend(candles.high, candles.low, candles.close)["SUPERT_7_3.0"]
        if (
                last_order_status.ready_to_procceed
                and last_order_status.is_long
                and super_trend[-2] > prev_close_price
                and super_trend[-1] < close_price
        ):
            return self._update_open_trade(
                TradeType.long.name, candles.close[-1], self.strategy_name, 0, candles.index[-1]
            )
        if (
                last_order_status.ready_to_procceed
                and last_order_status.is_short
                and super_trend[-2] < prev_close_price
                and super_trend[-1] > close_price
        ):
            return self._update_open_trade(
                TradeType.short.name, candles.close[-1], self.strategy_name, 0, candles.index[-1]
            )

    def exit_signal(self, candles, day_candles=None) -> bool:
        last_order_status = self._can_close_trade()
        close_price = candles.close[-1]
        super_trend = supertrend(candles.high, candles.low, candles.close)["SUPERT_7_3.0"]
        is_profit, take_profit = self._is_take_profit(candles)
        is_loss, stop_loss = self._is_stop_loss(candles)
        stop_date = last_order_status.entry_date + timedelta(hours=7)
        if last_order_status.ready_to_procceed \
                and last_order_status.is_long \
                and (stop_date == candles.index[-1] or super_trend[-1] > close_price):
            return self._update_close_trade(
                TradeType.short.name,
                candles.close[-1],
                self.strategy_name,
                candles.close[-1],
                candles.index[-1],
                False,
                False,
                take_profit,
                stop_loss,
            )

        if last_order_status.ready_to_procceed \
                and last_order_status.is_short \
                and (stop_date == candles.index[-1] or super_trend[-1] < close_price):
            return self._update_close_trade(
                TradeType.long.name,
                candles.close[-1],
                self.strategy_name,
                candles.close[-1],
                candles.index[-1],
                False,
                False,
                take_profit,
                stop_loss,
            )
