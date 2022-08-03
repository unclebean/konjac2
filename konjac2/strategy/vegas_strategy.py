from pandas_ta.overlap import ema
from .abc_strategy import ABCStrategy
from ..indicator.utils import TradeType


class VegasStrategy(ABCStrategy):
    strategy_name = "vegas tunnel"

    def __init__(self, symbol):
        ABCStrategy.__init__(self, symbol)

    def seek_trend(self, candles, middle_candles=None, long_candles=None):
        ema144 = ema(candles.close, 144)[-1]
        ema169 = ema(candles.close, 169)[-1]
        ema576 = ema(candles.close, 576)[-1]
        ema676 = ema(candles.close, 676)[-1]
        close_price = candles.close[-1]
        trend = None
        if close_price > ema676 and close_price > ema576 and close_price > ema169 and close_price > ema144:
            trend = TradeType.long.name
        if close_price < ema676 and close_price < ema576 and close_price < ema169 and close_price < ema144:
            trend = TradeType.short.name
        if trend is not None:
            self._delete_last_in_progress_trade()
            self._start_new_trade(trend, candles.index[-1])

    def entry_signal(self, candles, middle_candles=None, long_candles=None):
        ema12 = ema(candles.close, 12)[-1]
        ema144 = ema(candles.close, 144)
        ema676 = ema(candles.close, 676)
        close_price = candles.close[-1]
        prev_close_price = candles.close[-2]
        last_order_status = self._can_open_new_trade()
        if (
            last_order_status.ready_to_procceed
            and last_order_status.is_long
            and ema12 > ema144[-1]
            and prev_close_price < ema144[-2]
            and close_price > ema144[-1]
        ):
            self._update_open_trade(TradeType.long.name, candles.close[-1], "vegas", ema12, candles.index[-1])
        if (
            last_order_status.ready_to_procceed
            and last_order_status.is_short
            and ema12 < ema676[-1]
            and prev_close_price > ema676[-2]
            and close_price < ema676[-1]
        ):
            self._update_open_trade(TradeType.short.name, candles.close[-1], "vegas", ema12, candles.index[-1])

    def exit_signal(self, candles, middle_candles=None, long_candles=None):
        last_order_status = self._can_close_trade()
        if last_order_status.ready_to_procceed:
            last_trade = self.get_trade()
            high_price = candles.high[-1]
            low_price = candles.low[-1]
            position = last_trade.opened_position
            long_pctg = (high_price - position) / position
            short_pctg = (low_price - position) / position

            if last_order_status.is_long and (long_pctg > 0.008 or short_pctg > 0.004):
                self._update_close_trade(TradeType.short.name, candles.close[-1], "vegas", long_pctg, candles.index[-1])
            if last_order_status.is_short and (long_pctg > 0.004 or short_pctg > 0.008):
                self._update_close_trade(TradeType.short.name, candles.close[-1], "vegas", short_pctg, candles.index[-1])
