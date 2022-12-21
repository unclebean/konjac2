import logging

from pandas_ta import ema, supertrend
from .abc_strategy import ABCStrategy
from ..indicator.heikin_ashi_momentum import heikin_ashi_mom
from ..indicator.normalized_macd import n_macd
from ..indicator.utils import TradeType

log = logging.getLogger(__name__)


class NMacdVolatilityStrategy(ABCStrategy):
    strategy_name = "n-macd volatility"

    def __init__(self, symbol: str):
        ABCStrategy.__init__(self, symbol)

    def seek_trend(self, candles, day_candles=None):
        _, short_term_volatility = heikin_ashi_mom(day_candles, candles, rolling=42, holder_dev=21)
        trend = self._get_rsi_vwap_trend(candles)
        self._delete_last_in_progress_trade()
        ema_volatility = ema(short_term_volatility, 34)
        if trend is not None:
            self._start_new_trade(trend, candles.index[-1], open_type="volatility",
                                  h4_date=day_candles.index[-1])
            return
        if ema_volatility[-1] < short_term_volatility[-1]:
            self._start_new_trade(TradeType.long.name, candles.index[-1], open_type="volatility",
                                  h4_date=day_candles.index[-1])
        if ema_volatility[-1] > short_term_volatility[-1]:
            self._start_new_trade(TradeType.short.name, candles.index[-1], open_type="volatility",
                                  h4_date=day_candles.index[-1])

    def entry_signal(self, candles, day_candles=None):
        last_order_status = self._can_open_new_trade()
        trigger, macd_, _ = n_macd(candles.close, fast_length=12, slow_length=21)

        if (
                last_order_status.ready_to_procceed
                and last_order_status.is_long
                and macd_[-1] > trigger[-1]
                and macd_[-2] <= trigger[-2]
        ):
            return self._update_open_trade(
                TradeType.long.name, candles.close[-1], "n_macd", macd_[-1], candles.index[-1]
            )
        if (
                last_order_status.ready_to_procceed
                and last_order_status.is_short
                and macd_[-1] < trigger[-1]
                and macd_[-2] >= trigger[-2]
        ):
            return self._update_open_trade(
                TradeType.short.name, candles.close[-1], "n_macd", macd_[-1], candles.index[-1]
            )

        return False

    def exit_signal(self, candles, day_candles=None):
        last_order_status = self._can_close_trade()
        trigger, macd_, _ = n_macd(candles.close, fast_length=12, slow_length=21)
        is_profit, take_profit = self._is_take_profit(candles)
        is_loss, stop_loss = self._is_stop_loss(candles)

        if last_order_status.ready_to_procceed \
                and last_order_status.is_long \
                and (macd_[-1] < trigger[-1] or is_profit or is_loss):
            return self._update_close_trade(
                TradeType.short.name,
                candles.close[-1],
                "n_macd",
                macd_[-1],
                candles.index[-1],
                is_profit,
                is_loss,
                take_profit,
                stop_loss,
            )
        if last_order_status.ready_to_procceed \
                and last_order_status.is_short \
                and (macd_[-1] > trigger[-1] or is_profit or is_loss):
            return self._update_close_trade(
                TradeType.long.name,
                candles.close[-1],
                "n_macd",
                macd_[-1],
                candles.index[-1],
                is_profit,
                is_loss,
                take_profit,
                stop_loss,
            )
        return False
