from pandas_ta.overlap import sma
from pandas_ta.momentum import rsi
from .abc_strategy import ABCStrategy
from ..indicator.normalized_macd import n_macd
from ..indicator.utils import TradeType


class MacdRsiStrategy(ABCStrategy):
    strategy_name = "macd rsi strategy"
    indicator_macd = "macd"
    indicator_rsi = "rsi"
    indicator_ma = "ma"

    def __init__(self, symbol: str):
        ABCStrategy.__init__(self, symbol)

    def seek_trend(self, candles, middle_candles=None, long_candles=None):
        trigger, m_normal, _ = n_macd(candles.close)
        if trigger[-1] < 0 and trigger[-2] > m_normal[-2] and trigger[-1] < m_normal[-1]:
            self._delete_last_in_progress_trade()
            self._start_new_trade(TradeType.long.name, candles.index[-1])

        if trigger[-1] > 0 and trigger[-2] < m_normal[-2] and trigger[-1] > m_normal[-1]:
            self._delete_last_in_progress_trade()
            self._start_new_trade(TradeType.short.name, candles.index[-1])

    def entry_signal(self, candles, middle_candles=None, long_middle=None):
        last_order_status = self._can_open_new_trade()
        rsi_data = rsi(candles.close, timeperiod=21)
        rsi_sma_data = sma(rsi_data, 55)
        ma_data = self.ma(candles.close)
        if last_order_status.ready_to_procceed and last_order_status.is_long \
                and rsi_data[-1] > rsi_sma_data[-1] \
                and ma_data[-3] > candles.close[-3] \
                and ma_data[-2] < candles.close[-2] \
                and ma_data[-1] < candles.close[-1]:
            return self._update_open_trade(TradeType.long.name, candles.close[-1], "macd_rsi", ma_data[-1], candles.index[-1])
        if last_order_status.ready_to_procceed and last_order_status.is_short \
                and rsi_data[-1] < rsi_sma_data[-1] \
                and ma_data[-3] < candles.close[-3] \
                and ma_data[-2] > candles.close[-2] \
                and ma_data[-1] > candles.close[-1]:
            return self._update_open_trade(TradeType.short.name, candles.close[-1], "macd_rsi", ma_data[-1], candles.index[-1])

    def exit_signal(self, candles, middle_candles=None, long_candles=None):
        last_order_status = self._can_close_trade()
        is_profit, take_profit = self._is_take_profit(candles)
        is_loss, stop_loss = self._is_stop_loss(candles)
        ma_data = self.ma(candles.close)

        if last_order_status.ready_to_procceed and last_order_status.is_long \
                and (is_loss or is_profit):
            return self._update_close_trade(
                TradeType.short.name,
                candles.close[-1],
                "macd_rsi",
                candles.close[-1],
                candles.index[-1],
                is_profit,
                is_loss,
                take_profit,
                stop_loss,
            )

        if last_order_status.ready_to_procceed and last_order_status.is_short \
                and (is_loss or is_profit):
            return self._update_close_trade(
                TradeType.long.name,
                candles.close[-1],
                "macd_rsi",
                candles.close[-1],
                candles.index[-1],
                is_profit,
                is_loss,
                take_profit,
                stop_loss,
            )

    def ma(self, close, length=13):
        windows = close.rolling(length)
        moving_averages = windows.mean()
        moving_averages_list = moving_averages.tolist()

        return moving_averages_list[length - 1:]
