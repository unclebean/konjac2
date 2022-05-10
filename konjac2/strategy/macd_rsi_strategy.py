from pandas_ta.overlap import sma
from pandas_ta.momentum import macd, rsi
from abc_strategy import ABCStrategy
from ..models.trade import TradeStatus


class MacdRsiStrategy(ABCStrategy):
    strategy_name = "macd rsi strategy"
    indicator_macd = "macd"
    indicator_rsi = "rsi"
    indicator_ma = "ma"

    def __init__(self, symbol: str):
        ABCStrategy.__init__(self, symbol)

    def seek_trend(self, candles):
        pass

    def entry_signal(self, candles):
        last_trade = self.get_trade()
        if last_trade is not None and last_trade.status == TradeStatus.opened.name:
            ready_indicators = self._get_all_open_trade_signal_indicators(last_trade.id)
            if self.indicator_macd not in ready_indicators:
                macd_data = macd(candles.close, 13, 21)
                macd_series = macd_data["MACD_12_26_9"]
                macd_signal = macd_data["MACDs_12_26_9"]
                
        rsi_data = rsi(candles.close, timeperiod=21)
        rsi_sma_data = sma(rsi_data, 55)
        ma_data = sma(candles.close, 12)

    def exit_signal(self, candles):
        pass
