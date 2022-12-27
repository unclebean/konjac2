import logging
from datetime import datetime
from abc import ABC, abstractmethod

from .strategy_delegator import StrategyDelegator, LastTradeStatus
from ..chart.heikin_ashi import heikin_ashi

from ..indicator.utils import TradeType
from ..indicator.vwap import RSI_VWAP
from ..models.trade import get_last_time_trade

log = logging.getLogger(__name__)


class ABCStrategy(ABC):
    strategy_name = "abc strategy"
    balance = 4000

    def __init__(self, symbol: str, trade_short_order=True):
        self.symbol = symbol
        self.trade_short_order = trade_short_order

    @abstractmethod
    def seek_trend(self, candles, day_candles=None):
        pass

    @abstractmethod
    def entry_signal(self, candles, day_candles=None) -> bool:
        pass

    @abstractmethod
    def exit_signal(self, candles, day_candles=None) -> bool:
        pass

    def close_order_by_exchange(self, candles):
        StrategyDelegator.close_order_by_exchange(self.symbol, candles)

    def get_trade(self):
        return get_last_time_trade(self.symbol)

    def _can_open_new_trade(self) -> LastTradeStatus:
        return StrategyDelegator.can_open_new_trade(self.symbol)

    def _can_close_trade(self) -> LastTradeStatus:
        return StrategyDelegator.can_close_trade(self.symbol)

    def _delete_last_in_progress_trade(self):
        StrategyDelegator.delete_last_in_progress_trade(self.symbol)

    def _start_new_trade(self, trend: str, create_date=datetime.now(), open_type="", h4_date=None, trend_position=0):
        StrategyDelegator.start_new_trade(self.symbol, self.strategy_name, trend, create_date, open_type, h4_date,
                                          trend_position)

    def _update_open_trade(self, trade_type, position, indicator, indicator_value=0, entry_date=datetime.now()):
        self.balance = StrategyDelegator.update_open_trade(self.symbol, self.balance, trade_type, position, indicator,
                                                           indicator_value, entry_date)
        return True

    def _update_close_trade(
            self,
            trade_type,
            position,
            indicator,
            indicator_value=0,
            exit_date=datetime.now(),
            is_profit=False,
            is_loss=False,
            take_profit=0,
            stop_loss=0,
    ):
        self.balance += StrategyDelegator.update_close_trade(self.symbol, trade_type, position, indicator,
                                                             indicator_value, exit_date, is_profit, is_loss,
                                                             take_profit, stop_loss)
        return True

    def _get_all_open_trade_signal_indicators(self, trade_id: str):
        return StrategyDelegator.get_all_open_trade_signal_indicators(trade_id)

    def _is_take_profit(self, candles):
        return StrategyDelegator.is_take_profit(self.symbol, candles)

    def _is_stop_loss(self, candles):
        return StrategyDelegator.is_stop_loss(self.symbol, candles)

    def _get_longer_timeframe_volatility(self, candles, longer_timeframe_candles, rolling=7, holder_dev=3):
        daily_volatility = (longer_timeframe_candles["high"] - longer_timeframe_candles["low"]) / \
                           longer_timeframe_candles["high"]
        average_dv = daily_volatility[-7:].abs().sum() / 7
        # volatility/3 for the threadholder
        threadholder = average_dv / 3
        # getting 6H heikin_ashi
        # close - open for volatility of heikin_ashi bar
        hc = heikin_ashi(candles)
        h6_volatility = (hc["close"] - hc["open"]) / hc["close"]
        h6_volatility = h6_volatility.values[-1]

        if threadholder <= abs(h6_volatility) and h6_volatility > 0:
            return TradeType.long.name

        if threadholder <= abs(h6_volatility) and h6_volatility < 0:
            return TradeType.short.name

        return None

    def _get_rsi_vwap_trend(self, candles):
        r_vwap = RSI_VWAP(candles, group_by="week")
        if r_vwap[-3] < 5 and r_vwap[-2] < 5 and r_vwap[-1] < 5:
            return TradeType.short.name
        if r_vwap[-3] > 95 and r_vwap[-2] > 95 and r_vwap[-1] > 95:
            return TradeType.long.name

        return None
