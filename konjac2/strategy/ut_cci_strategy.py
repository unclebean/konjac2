
from pandas_ta import cci, ema

from konjac2.indicator.squeeze_momentum import is_squeeze
from konjac2.indicator.ut_bot import ut_bot
from konjac2.indicator.utils import TradeType
from konjac2.strategy.abc_strategy import ABCStrategy


class UTCCIStrategy(ABCStrategy):
    strategy_name = "ut cci"

    def seek_trend(self, candles, day_candles=None):
        pd_data = ut_bot(candles)
        if pd_data['Buy'].iat[-1]:
            self._delete_last_in_progress_trade()
            self._start_new_trade(TradeType.long.name, candles.index[-1], h4_date=day_candles.index[-1])
        if pd_data['Sell'].iat[-1]:
            self._delete_last_in_progress_trade()
            self._start_new_trade(TradeType.short.name, candles.index[-1], h4_date=day_candles.index[-1])

    def entry_signal(self, candles, day_candles=None) -> bool:
        is_sqz = is_squeeze(candles)
        cci7 = cci(candles.high, candles.low, candles.close, 7)
        ema_30 = ema(candles.close, 30)
        last_order_status = self._can_open_new_trade()
        if (
                last_order_status.ready_to_procceed
                and last_order_status.is_long
                and not is_sqz
                and cci7[-1] > 100
                and ema_30[-1] < candles.close[-1]
        ):
            return self._update_open_trade(
                TradeType.long.name, candles.close[-1], self.strategy_name, 0, candles.index[-1]
            )
        if (
                last_order_status.ready_to_procceed
                and last_order_status.is_short
                and not is_sqz
                and cci7[-1] < -100
                and ema_30[-1] > candles.close[-1]
        ):
            return self._update_open_trade(
                TradeType.short.name, candles.close[-1], self.strategy_name, 0, candles.index[-1]
            )

    def exit_signal(self, candles, day_candles=None) -> bool:
        last_order_status = self._can_close_trade()
        pd_data = ut_bot(candles)
        is_profit, take_profit = self._is_take_profit(candles)
        is_loss, stop_loss = self._is_stop_loss(candles)
        if last_order_status.ready_to_procceed \
                and last_order_status.is_long \
                and (is_profit or is_loss or pd_data['Sell'].iat[-1]):
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
                and (is_profit or is_loss or pd_data['Buy'].iat[-1]):
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
