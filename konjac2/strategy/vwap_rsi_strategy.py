import logging

from .abc_strategy import ABCStrategy
from ..indicator.bb_cci_momentum import cci_entry_exit_signal
from ..indicator.utils import TradeType
from ..indicator.vwap import RSI_VWAP

log = logging.getLogger(__name__)


class VwapRsiStrategy(ABCStrategy):
    strategy_name = "vwap rsi"

    def __init__(self, symbol: str):
        ABCStrategy.__init__(self, symbol)

    def seek_trend(self, candles, day_candles=None):
        r_vwap = RSI_VWAP(candles, group_by="week")
        self._delete_last_in_progress_trade()
        if r_vwap[-1] > 85:
            self._start_new_trade(TradeType.long.name, candles.index[-1], open_type="vwap rsi",
                                  h4_date=day_candles.index[-1], trend_position=candles.close[-1])
        if r_vwap[-1] < 15:
            self._start_new_trade(TradeType.short.name, candles.index[-1], open_type="vwap rsi",
                                  h4_date=day_candles.index[-1], trend_position=candles.close[-1])

    def entry_signal(self, candles, day_candles=None):
        last_order_status = self._can_open_new_trade()
        _, cci_34, cci_144 = cci_entry_exit_signal(candles)

        if (
                last_order_status.ready_to_procceed
                and last_order_status.is_long
                and cci_34[-2] <= cci_144[-2]
                and cci_34[-1] > cci_144[-1]
        ):
            return self._update_open_trade(
                TradeType.long.name, candles.close[-1], "vwap rsi", 0, candles.index[-1]
            )
        if (
                last_order_status.ready_to_procceed
                and last_order_status.is_short
                and cci_34[-2] >= cci_144[-2]
                and cci_34[-1] < cci_144[-1]
        ):
            return self._update_open_trade(
                TradeType.short.name, candles.close[-1], "vwap rsi", 0, candles.index[-1]
            )

        return False

    def exit_signal(self, candles, day_candles=None):
        last_order_status = self._can_close_trade()
        _, cci_34, cci_144 = cci_entry_exit_signal(candles)
        is_profit, take_profit = self._is_take_profit(candles)
        is_loss, stop_loss = self._is_stop_loss(candles)

        if last_order_status.ready_to_procceed \
                and last_order_status.is_long \
                and (cci_34[-1] <= cci_144[-1] or is_profit or is_loss):
            return self._update_close_trade(
                TradeType.short.name,
                candles.close[-1],
                "vwap rsi",
                cci_34[-1],
                candles.index[-1],
                is_profit,
                is_loss,
                take_profit,
                stop_loss,
            )
        if last_order_status.ready_to_procceed \
                and last_order_status.is_short \
                and (cci_34[-1] >= cci_144[-1] or is_profit or is_loss):
            return self._update_close_trade(
                TradeType.long.name,
                candles.close[-1],
                "vwap rsi",
                cci_34[-1],
                candles.index[-1],
                is_profit,
                is_loss,
                take_profit,
                stop_loss,
            )
        return False
