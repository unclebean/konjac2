from konjac2.indicator.don_chain_channels import don_chain_channels
from konjac2.indicator.rsi_trend import rsi_trend
from konjac2.indicator.utils import TradeType
from konjac2.strategy.abc_strategy import ABCStrategy


class RsiTrendDonChainStrategy(ABCStrategy):
    strategy_name = "rsi trend don chain"

    def __init__(self, symbol: str, trade_short_order=True, trade_long_order=True):
        ABCStrategy.__init__(self, symbol, trade_short_order, trade_long_order)

    def seek_trend(self, candles, day_candles=None):
        trend = rsi_trend(candles)
        self._delete_last_in_progress_trade()
        if trend[-1] > 0:
            self._start_new_trade(TradeType.long.name, candles.index[-1], h4_date=day_candles.index[-1])
        if trend[-1] < 0:
            self._start_new_trade(TradeType.short.name, candles.index[-1], h4_date=day_candles.index[-1])

    def entry_signal(self, candles, day_candles=None) -> bool:
        last_order_status = self._can_open_new_trade()
        upper_don, _, lower_don = don_chain_channels(candles)
        if (
                last_order_status.ready_to_procceed
                and last_order_status.is_long
                and lower_don[-2] == lower_don[-1]
                and lower_don[-2] >= candles.close[-2]
                and lower_don[-1] < candles.close[-1]
        ):
            return self._update_open_trade(
                TradeType.long.name, candles.close[-1], self.strategy_name, 0, candles.index[-1]
            )
        if (
                last_order_status.ready_to_procceed
                and last_order_status.is_short
                and upper_don[-2] == upper_don[-1]
                and upper_don[-2] <= candles.close[-2]
                and upper_don[-1] > candles.close[-1]
        ):
            return self._update_open_trade(
                TradeType.short.name, candles.close[-1], self.strategy_name, 0, candles.index[-1]
            )

    def exit_signal(self, candles, day_candles=None) -> bool:
        last_order_status = self._can_close_trade()
        _, mid_don, _ = don_chain_channels(candles)
        is_profit, take_profit = self._is_take_profit(candles)
        is_loss, stop_loss = self._is_stop_loss(candles)
        if last_order_status.ready_to_procceed \
                and last_order_status.is_long \
                and (is_profit or is_loss or mid_don[-1] < candles.close[-1]):
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
                and (is_profit or is_loss or mid_don[-1] > candles.close[-1]):
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
