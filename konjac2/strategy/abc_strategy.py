from collections import namedtuple
from datetime import datetime
from abc import ABC, abstractclassmethod

from ..indicator.utils import TradeType
from ..models import apply_session
from ..models.trade import Trade, TradeStatus, get_last_time_trade
from ..models.signal import Signal

LastTradeStatus = namedtuple("LastTradeStatus", "ready_to_procceed is_long is_short")


class ABCStrategy(ABC):
    strategy_name = "abc strategy"

    def __init__(self, symbol: str):
        self.symbol = symbol

    @abstractclassmethod
    def seek_trend(self, candles):
        pass

    @abstractclassmethod
    def entry_signal(self, candles):
        pass

    @abstractclassmethod
    def exit_signal(self, candles):
        pass

    def get_trade(self):
        return get_last_time_trade(self.symbol)

    def _can_open_new_trade(self) -> LastTradeStatus:
        last_trade = get_last_time_trade(self.symbol)
        ready_to_new_trade = (
            last_trade is not None
            and last_trade.status != TradeStatus.closed.name
            and last_trade.status != TradeStatus.opened.name
        )
        is_long = ready_to_new_trade and last_trade.trend == TradeType.long.name
        is_short = ready_to_new_trade and last_trade.trend == TradeType.short.name
        return LastTradeStatus(ready_to_new_trade, is_long, is_short)

    def _can_close_trade(self) -> LastTradeStatus:
        last_trade = get_last_time_trade(self.symbol)
        ready_to_close = last_trade is not None and last_trade.status == TradeStatus.opened.name
        is_long = ready_to_close and last_trade.trend == TradeType.long.name
        is_short = ready_to_close and last_trade.trend == TradeType.short.name
        return LastTradeStatus(ready_to_close, is_long, is_short)

    def _delete_last_in_progress_trade(self):
        last_trade = get_last_time_trade(self.symbol)
        if last_trade is not None and last_trade.status == TradeStatus.in_progress.name:
            session = apply_session()
            session.delete(last_trade)
            session.commit()
            session.close()

    def _start_new_trade(self, trend: str, create_date=datetime.now()):
        last_trade = get_last_time_trade(self.symbol)
        if last_trade is None or last_trade is not None and last_trade.status == TradeStatus.closed.name:
            session = apply_session()
            session.add(
                Trade(
                    symbol=self.symbol,
                    strategy=self.strategy_name,
                    trend=trend,
                    status=TradeStatus.in_progress.name,
                    create_date=create_date,
                )
            )
            session.commit()
            session.close()

    def _update_open_trade(self, tradeType, position, indicator, indicator_value=0, entry_date=datetime.now()):
        last_trade = get_last_time_trade(self.symbol)
        session = apply_session()
        if last_trade is None:
            return
        session.delete(last_trade)
        last_trade.entry_signal = tradeType
        last_trade.entry_date = entry_date
        last_trade.status = TradeStatus.opened.name
        last_trade.opened_position = position
        session.add(last_trade)
        session.add(
            Signal(
                symbol=self.symbol,
                indicator=indicator,
                indicator_value=str(indicator_value),
                trade_signal=tradeType,
                trade_status=TradeStatus.opened.name,
                trade_id=last_trade.id,
            )
        )
        session.commit()
        session.close()

    def _update_close_trade(self, tradeType, position, indicator, indicator_value=0, exit_date=datetime.now()):
        last_trade = get_last_time_trade(self.symbol)
        session = apply_session()
        if last_trade is None or last_trade.opened_position is None:
            return
        result = (
            last_trade.opened_position - position
            if last_trade.trend == TradeType.short.name
            else position - last_trade.opened_position
        )
        session.delete(last_trade)
        last_trade.exit_signal = tradeType
        last_trade.exit_date = exit_date
        last_trade.status = TradeStatus.closed.name
        last_trade.closed_position = position
        last_trade.result = result
        session.add(last_trade)
        session.add(
            Signal(
                symbol=self.symbol,
                indicator=indicator,
                indicator_value=str(indicator_value),
                trade_signal=tradeType,
                trade_status=TradeStatus.closed.name,
                trade_id=last_trade.id,
            )
        )
        session.commit()
        session.close()
