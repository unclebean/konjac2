from pandas_ta import ema

from konjac2.chart.heikin_ashi import heikin_ashi
from konjac2.indicator.utils import TradeType
from konjac2.strategy.abc_strategy import ABCStrategy


class StrategyOne(ABCStrategy):
    def seek_trend(self, candles, day_candles=None):
        if self._is_buy(candles):
            self._delete_last_in_progress_trade()
            self._start_new_trade(TradeType.long.name, candles.index[-1])

    def entry_signal(self, candles, day_candles=None) -> bool:
        last_order_status = self._can_open_new_trade()

        if (
                last_order_status.ready_to_procceed
                and last_order_status.is_long
        ):
            return self._update_open_trade(
                TradeType.long.name, candles.close[-1], "strategy 1", 0, candles.index[-1]
            )

    def exit_signal(self, candles, day_candles=None) -> bool:
        last_order_status = self._can_close_trade()
        if last_order_status.ready_to_procceed \
                and last_order_status.is_long \
                and self._is_exit_buy(candles):
            return self._update_close_trade(
                TradeType.short.name,
                candles.close[-1],
                "strategy 5",
                candles.close[-1],
                candles.index[-1],
                False,
                False,
                0,
                0,
            )

    def _is_buy(self, candles):
        ema_20 = ema(candles.close, 20)
        ema_50 = ema(candles.close, 50)
        heikin_chart = heikin_ashi(candles)
        ha_open = heikin_chart.open
        ha_close = heikin_chart.close

        return ema_50[-1] < ema_20[-1] < ha_close[-1] \
               and ema_20[-2] < ema_50[-2] \
               and ha_open[-1] < ha_close[-1]

    def _is_exit_buy(self, candles):
        ema_20 = ema(candles.close, 20)
        ema_50 = ema(candles.close, 50)
        ema_100 = ema(candles.close, 100)
        heikin_chart = heikin_ashi(candles)
        ha_open = heikin_chart.open
        ha_close = heikin_chart.close

        return (ema_50[-1] > ema_100[-1] and ema_50[-2] < ema_100[-2]) \
               or ha_close[-1] < ema_20[-1] \
               or ha_open[-1] > ha_close[-1]
