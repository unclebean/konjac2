import logging

from pandas_ta import bbands, stoch

from .abc_strategy import ABCStrategy
from ..indicator.heikin_ashi_momentum import heikin_ashi_mom
from ..indicator.utils import TradeType

log = logging.getLogger(__name__)


class BBStochStrategy(ABCStrategy):
    strategy_name = "bb stoch"

    def __init__(self, symbol: str):
        ABCStrategy.__init__(self, symbol)

    def seek_trend(self, candles, day_candles=None):
        close_price = candles.close
        bb_55 = bbands(candles.close, 34)
        bb_55_low = bb_55["BBL_34_2.0"]
        bb_55_up = bb_55["BBU_34_2.0"]
        trend = None
        if bb_55_up[-3] < close_price[-3] \
                and bb_55_up[-2] < close_price[-2] \
                and bb_55_up[-1] < close_price[-1]:
            trend = TradeType.long.name
        if bb_55_low[-3] > close_price[-3] \
                and bb_55_low[-2] > close_price[-2] \
                and bb_55_low[-1] > close_price[-1]:
            trend = TradeType.short.name
        if trend is not None:
            self._delete_last_in_progress_trade()
            self._start_new_trade(trend, candles.index[-1])

    # def seek_trend(self, candles, day_candles=None):
    #     thread_holder, short_term_volatility = heikin_ashi_mom(day_candles, candles, rolling=42, holder_dev=21)
    #     self._delete_last_in_progress_trade()
    #     if thread_holder[-1] > short_term_volatility[-1] > short_term_volatility[-2]:
    #         self._start_new_trade(TradeType.long.name, candles.index[-1])
    #     if thread_holder[-1] < short_term_volatility[-1] < short_term_volatility[-2]:
    #         self._start_new_trade(TradeType.short.name, candles.index[-1])

    def entry_signal(self, candles, day_candles=None):
        thread_holder, short_term_volatility = heikin_ashi_mom(day_candles, candles, rolling=42, holder_dev=21)
        last_order_status = self._can_open_new_trade()
        if last_order_status.ready_to_procceed \
                and last_order_status.is_long \
                and thread_holder[-1] < short_term_volatility[-1] and thread_holder[-2] > short_term_volatility[-2]:
            return self._update_open_trade(TradeType.long.name, candles.close[-1], "bb stoch", 0, candles.index[-1])

        if last_order_status.ready_to_procceed \
                and last_order_status.is_short \
                and thread_holder[-1] > short_term_volatility[-1] and thread_holder[-2] < short_term_volatility[-2]:
            return self._update_open_trade(TradeType.short.name, candles.close[-1], "bb stoch", 0, candles.index[-1])
            # say_something(f"{self.symbol} open {TradeType.short.name}")

    def exit_signal(self, candles, day_candles=None):
        _, short_term_volatility = heikin_ashi_mom(day_candles, candles, rolling=42, holder_dev=21)
        last_order_status = self._can_close_trade()
        is_profit, take_profit = self._is_take_profit(candles)
        is_loss, stop_loss = self._is_stop_loss(candles)
        if last_order_status.ready_to_procceed and last_order_status.is_long \
                and (short_term_volatility[-1] < short_term_volatility[-2] or candles.close[-1] < candles.open[-1] or is_loss or is_profit):
            return self._update_close_trade(
                TradeType.short.name,
                candles.close[-1],
                "bb stoch",
                0,
                candles.index[-1],
                is_profit,
                is_loss,
                take_profit,
                stop_loss,
            )

        if last_order_status.ready_to_procceed and last_order_status.is_short \
                and (short_term_volatility[-1] > short_term_volatility[-2] or candles.close[-1] > candles.open[-1] or is_loss or is_profit):
            return self._update_close_trade(
                TradeType.long.name,
                candles.close[-1],
                "bb stoch",
                0,
                candles.index[-1],
                is_profit,
                is_loss,
                take_profit,
                stop_loss,
            )
