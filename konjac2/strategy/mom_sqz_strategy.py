from datetime import timedelta

from pandas_ta import kc, bbands, mom

from konjac2.indicator.squeeze_momentum import squeeze
from konjac2.indicator.ut_bot import ut_bot
from konjac2.indicator.utils import TradeType
from konjac2.strategy.abc_strategy import ABCStrategy


class MomentumSqueezeStrategy(ABCStrategy):
    strategy_name = "momentum squeeze"

    def __init__(self, symbol: str, trade_short_order=True):
        ABCStrategy.__init__(self, symbol, trade_short_order)

    def seek_trend(self, candles, day_candles=None):
        pd_data = ut_bot(candles)
        if pd_data['Buy'].iat[-1]:
            self._delete_last_in_progress_trade()
            self._start_new_trade(TradeType.long.name, candles.index[-1], h4_date=day_candles.index[-1])
        if pd_data['Sell'].iat[-1] and self.trade_short_order:
            self._delete_last_in_progress_trade()
            self._start_new_trade(TradeType.short.name, candles.index[-1], h4_date=day_candles.index[-1])


    def entry_signal(self, candles, day_candles=None):
        last_order_status = self._can_open_new_trade()
        kcdf = kc(candles.high, candles.low, candles.close, length=20, scalar=1.5, mamode="sma", tr=True)
        bbandsdf = bbands(candles.close, length=20, std=2, mamode="sma")

        lowerKC = kcdf["KCLs_20_1.5"].round(4)
        upperKC = kcdf["KCUs_20_1.5"].round(4)
        lowerBB = bbandsdf["BBL_20_2.0"].round(4)
        upperBB = bbandsdf["BBU_20_2.0"].round(4)
        if last_order_status.ready_to_procceed \
                and last_order_status.is_long and lowerBB[-2] < lowerKC[-2] and lowerBB[-1] > lowerKC[-1]:
            return self._update_open_trade(TradeType.long.name, candles.close[-1], "ema_34", 0, candles.index[-1])
            # say_something(f"{self.symbol} open {TradeType.long.name}")

        if last_order_status.ready_to_procceed \
                and last_order_status.is_short and upperBB[-2] < upperKC[-2] and upperBB[-1] > upperKC[-1]:
            return self._update_open_trade(TradeType.short.name, candles.close[-1], "ema_34", 0, candles.index[-1])
            # say_something(f"{self.symbol} open {TradeType.short.name}")


    def exit_signal(self, candles, day_candles=None):
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
                is_profit,
                is_loss,
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
                is_profit,
                is_loss,
                take_profit,
                stop_loss,
            )
