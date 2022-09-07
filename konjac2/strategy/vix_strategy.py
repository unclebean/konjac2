from pandas_ta import sma

from konjac2.indicator.kalman_filter import kalman_candles
from konjac2.indicator.utils import TradeType
from konjac2.strategy.abc_strategy import ABCStrategy


def _get_signals(candles):
    close = kalman_candles(candles).close
    vix = close / close.shift(90) - 1
    ma90 = sma(vix, 90)
    vix_up = ma90.rolling(window=90).max().shift(1)
    vix_down = ma90.rolling(window=90).min().shift(1)
    is_long = vix[-1] > vix_up[-1] and vix[-2] <= vix_up[-2]
    is_short = vix[-1] < vix_down[-1] and vix[-2] >= vix_down[-2]

    return is_long, is_short


def _get_emv(candles):
    hp = candles.high
    lp = candles.low
    vol = candles.volume
    mid = (hp[-1] + lp[-1]) / 2 - (hp[-2] + lp[-2]) / 2
    ratio = (vol[-1] / 10000) / (hp[-1] - lp[-1])
    emv = mid / ratio

    return emv


class VixStrategy(ABCStrategy):
    strategy_name = "vix strategy"

    def seek_trend(self, candles, day_candles=None):
        is_long, is_short = _get_signals(candles)
        emv_ = _get_emv(candles)
        if is_long and emv_ > 0:
            self._delete_last_in_progress_trade()
            self._start_new_trade(TradeType.long.name, candles.index[-1], h4_date=day_candles.index[-1])
        if is_short and emv_ > 0:
            self._delete_last_in_progress_trade()
            self._start_new_trade(TradeType.short.name, candles.index[-1], h4_date=day_candles.index[-1])

    def entry_signal(self, candles, day_candles=None) -> bool:
        last_order_status = self._can_open_new_trade()
        if (
                last_order_status.ready_to_procceed
                and last_order_status.is_long
        ):
            return self._update_open_trade(
                TradeType.long.name, candles.close[-1], self.strategy_name, 0, candles.index[-1]
            )
        if (
                last_order_status.ready_to_procceed
                and last_order_status.is_short
        ):
            return self._update_open_trade(
                TradeType.short.name, candles.close[-1], self.strategy_name, 0, candles.index[-1]
            )

    def exit_signal(self, candles, day_candles=None) -> bool:
        last_order_status = self._can_close_trade()
        is_profit, take_profit = self._is_take_profit(candles)
        is_loss, stop_loss = self._is_stop_loss(candles)
        is_long, is_short = _get_signals(candles)
        emv_ = _get_emv(candles)
        if last_order_status.ready_to_procceed \
                and last_order_status.is_long \
                and (is_short or is_profit or is_loss or emv_ < 0):
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
                and (is_long or is_profit or is_loss or emv_ < 0):
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
