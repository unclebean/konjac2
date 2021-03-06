import logging
from collections import namedtuple
from datetime import datetime
from abc import ABC, abstractclassmethod

from konjac2.indicator.heikin_ashi_momentum import heikin_ashi_mom

from ..indicator.utils import TradeType
from ..models import apply_session
from ..models.trade import Trade, TradeStatus, get_last_time_trade
from ..models.signal import Signal, get_open_trade_signals

LastTradeStatus = namedtuple("LastTradeStatus", "ready_to_procceed is_long is_short opened_position")

log = logging.getLogger(__name__)


class ABCStrategy(ABC):
    strategy_name = "abc strategy"
    balance = 500

    def __init__(self, symbol: str):
        self.symbol = symbol

    @abstractclassmethod
    def seek_trend(self, candles):
        pass

    @abstractclassmethod
    def entry_signal(self, candles) -> bool:
        pass

    @abstractclassmethod
    def exit_signal(self, candles) -> bool:
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
        opened_position = last_trade.opened_position if ready_to_new_trade else 0
        return LastTradeStatus(ready_to_new_trade, is_long, is_short, opened_position)

    def _can_close_trade(self) -> LastTradeStatus:
        last_trade = get_last_time_trade(self.symbol)
        ready_to_close = last_trade is not None and last_trade.status == TradeStatus.opened.name
        is_long = ready_to_close and last_trade.trend == TradeType.long.name
        is_short = ready_to_close and last_trade.trend == TradeType.short.name
        opened_position = last_trade.opened_position if ready_to_close else 0
        return LastTradeStatus(ready_to_close, is_long, is_short, opened_position)

    def _delete_last_in_progress_trade(self):
        last_trade = get_last_time_trade(self.symbol)
        if last_trade is not None and last_trade.status == TradeStatus.in_progress.name:
            session = apply_session()
            session.delete(last_trade)
            session.commit()
            session.close()

    def _start_new_trade(self, trend: str, create_date=datetime.now(), open_type="", h4_date=None):
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
                    open_type=open_type,
                    h4_date=h4_date,
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
        last_trade.quantity = self.balance / position
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
        self.balance = self.balance - last_trade.quantity * position
        gain = (last_trade.quantity * position + last_trade.quantity * position * 0.3) / last_trade.quantity
        loss = (last_trade.quantity * position - last_trade.quantity * position * 0.15) / last_trade.quantity
        log.info(f"{self.symbol} take profit {gain} stop loss {loss}")

        session.commit()
        session.close()
        return True

    def _update_close_trade(
            self,
            tradeType,
            position,
            indicator,
            indicator_value=0,
            exit_date=datetime.now(),
            is_profit=False,
            is_loss=False,
            take_profit=0,
            stop_loss=0,
    ):
        last_trade = get_last_time_trade(self.symbol)
        session = apply_session()
        if last_trade is None or last_trade.opened_position is None:
            return

        session.delete(last_trade)
        last_trade.exit_signal = tradeType
        last_trade.exit_date = exit_date
        last_trade.status = TradeStatus.closed.name
        last_trade.closed_position = position

        result = (
                     last_trade.opened_position - position
                     if last_trade.trend == TradeType.short.name
                     else position - last_trade.opened_position
                 ) * last_trade.quantity

        if is_profit:
            result = take_profit
        if is_loss:
            result = -stop_loss

        fee = (last_trade.opened_position * (0.061110 / 100) * last_trade.quantity) + (
                last_trade.closed_position * (0.061110 / 100) * last_trade.quantity
        )
        self.balance += last_trade.opened_position * last_trade.quantity + result - fee
        # print("balance is {}".format(self.balance))
        last_trade.result = result - fee
        # print("close order result {} fee {}".format(result - fee, fee))
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
        return True

    def _get_all_open_trade_signal_indicators(self, trade_id: str):
        signals = get_open_trade_signals(trade_id)
        return list(map(lambda s: s.indicator, signals))

    def _is_take_profit(self, candles):
        last_trade = self.get_trade()
        if last_trade is not None and last_trade.status == TradeStatus.opened.name:
            low_price = candles.low[-1]
            high_price = candles.high[-1]

            take_profit = last_trade.opened_position * last_trade.quantity * 0.04

            profit = (high_price - last_trade.opened_position) * last_trade.quantity
            if last_trade.trend == TradeType.short.name:
                profit = (last_trade.opened_position - low_price) * last_trade.quantity

            """
            print(
                "high: {} low: {} position: {} quantity: {} result: {} take profit: {}".format(
                    high_price, low_price, last_trade.opened_position, last_trade.quantity, profit, take_profit
                )
            )
            """

            return profit >= take_profit, take_profit

    def _is_stop_loss(self, candles):
        last_trade = self.get_trade()
        if last_trade is not None and last_trade.status == TradeStatus.opened.name:
            # close_price = candles.close[-1]
            low_price = candles.low[-1]
            high_price = candles.high[-1]

            stop_loss = last_trade.opened_position * last_trade.quantity * 0.015

            loss = (last_trade.opened_position - low_price) * last_trade.quantity
            if last_trade.trend == TradeType.short.name:
                loss = (high_price - last_trade.opened_position) * last_trade.quantity

            # print(last_trade)
            # print(last_trade.opened_position, close_price, low_price, high_price, last_trade.quantity)
            # print("loss: {} stop loss:: {}".format(loss, stop_loss))

            return loss >= stop_loss, stop_loss

    def _get_longer_timeframe_volatility(self, candles, longer_timeframe_candles, rolling=3, holder_dev=2):
        threadholder, short_term_volatility = heikin_ashi_mom(candles, longer_timeframe_candles, rolling=rolling,
                                                              holder_dev=holder_dev)
        trend_action = None
        if threadholder[-1] <= abs(short_term_volatility[-1]) and short_term_volatility[-1] > 0:
            trend_action = TradeType.long.name

        if threadholder[-1] <= abs(short_term_volatility[-1]) and short_term_volatility[-1] < 0:
            trend_action = TradeType.short.name

        return trend_action
