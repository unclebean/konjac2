from konjac2.chart.heikin_ashi import sma_heikin_ashi
from konjac2.indicator.utils import TradeType
from konjac2.strategy.abc_strategy import ABCStrategy


class SmoothedHAStrategy(ABCStrategy):
    strategy_name = "smoothed_ha"

    def __init__(self, symbol: str):
        ABCStrategy.__init__(self, symbol)

    def seek_trend(self, candles, day_candles=None):
        is_long, is_short = self._get_signal(candles)
        trend = None
        if is_long:
            trend = TradeType.long.name
        if is_short:
            trend = TradeType.short.name
        if trend is not None:
            self._delete_last_in_progress_trade()
            self._start_new_trade(trend, candles.index[-1])

    def entry_signal(self, candles, day_candles=None):
        is_long, is_short = self._get_signal(candles)
        last_order_status = self._can_open_new_trade()
        if last_order_status.ready_to_procceed \
                and last_order_status.is_long \
                and is_long:
            return self._update_open_trade(TradeType.long.name, candles.close[-1], "ema_34", 0,
                                           candles.index[-1])
            # say_something(f"{self.symbol} open {TradeType.long.name}")

        if last_order_status.ready_to_procceed \
                and last_order_status.is_short \
                and is_short:
            return self._update_open_trade(TradeType.short.name, candles.close[-1], "ema_34", 0,
                                           candles.index[-1])
            # say_something(f"{self.symbol} open {TradeType.short.name}")

    def exit_signal(self, candles, day_candles=None):
        is_long_exit, is_short_exit = self._get_exit_signal(candles)
        last_order_status = self._can_close_trade()
        is_profit, take_profit = self._is_take_profit(candles)
        is_loss, stop_loss = self._is_stop_loss(candles)
        if last_order_status.ready_to_procceed and last_order_status.is_long \
                and (is_long_exit or is_loss or is_profit):
            return self._update_close_trade(
                TradeType.short.name,
                candles.close[-1],
                "ema_34",
                0,
                candles.index[-1],
                is_profit=is_profit,
                is_loss=is_loss,
                take_profit=take_profit,
                stop_loss=stop_loss,
            )

        if last_order_status.ready_to_procceed and last_order_status.is_short \
                and (is_short_exit or is_loss or is_profit):
            return self._update_close_trade(
                TradeType.long.name,
                candles.close[-1],
                "ema_34",
                0,
                candles.index[-1],
                is_profit=is_profit,
                is_loss=is_loss,
                take_profit=take_profit,
                stop_loss=stop_loss,
            )

    def _get_signal(self, candles):
        cha, oha, _, _ = sma_heikin_ashi(candles)
        is_long = candles.close[-1] > cha[-1] > oha[-1] > candles.open[-1]
        is_short = candles.close[-1] < cha[-1] < oha[-1] < candles.open[-1]
        return is_short, is_long

    def _get_exit_signal(self, candles):
        cha, oha, _, _ = sma_heikin_ashi(candles)
        is_long_exit = cha[-1] < oha[-1]
        is_short_exit = cha[-1] > oha[-1]
        return is_short_exit, is_long_exit
