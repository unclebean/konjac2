import logging
from collections import namedtuple
from datetime import datetime

from pandas_ta import atr

from konjac2.indicator.utils import TradeType
from konjac2.models import Signal, apply_session
from konjac2.models.signal import get_open_trade_signals
from konjac2.models.trade import TradeStatus, get_last_time_trade, Trade
from konjac2.service.utils import get_take_profit, get_stop_loss

LastTradeStatus = namedtuple("LastTradeStatus", "ready_to_procceed is_long is_short opened_position, entry_date")

log = logging.getLogger(__name__)


class StrategyDelegator:
    @classmethod
    def close_order_by_exchange(cls, symbol: str, candles) -> object:
        last_order_status = cls.can_close_trade(symbol)
        is_profit, take_profit = cls.is_take_profit(symbol, candles)
        is_loss, stop_loss = cls.is_stop_loss(symbol, candles)
        if last_order_status.ready_to_procceed and last_order_status.is_long:
            return cls.update_close_trade(
                symbol,
                TradeType.short.name,
                candles.close[-1],
                "exchange",
                0,
                candles.index[-1],
                is_profit,
                is_loss,
                take_profit,
                stop_loss,
            )

        if last_order_status.ready_to_procceed and last_order_status.is_short:
            return cls.update_close_trade(
                symbol,
                TradeType.long.name,
                candles.close[-1],
                "exchange",
                0,
                candles.index[-1],
                is_profit,
                is_loss,
                take_profit,
                stop_loss,
            )

    @staticmethod
    def get_trade(symbol: str):
        return get_last_time_trade(symbol)

    @staticmethod
    def can_open_new_trade(symbol: str) -> LastTradeStatus:
        last_trade = get_last_time_trade(symbol)
        ready_to_new_trade = (
                last_trade is not None
                and last_trade.status != TradeStatus.closed.name
                and last_trade.status != TradeStatus.opened.name
        )
        is_long = ready_to_new_trade and last_trade.trend == TradeType.long.name
        is_short = ready_to_new_trade and last_trade.trend == TradeType.short.name
        opened_position = last_trade.opened_position if ready_to_new_trade else 0
        return LastTradeStatus(ready_to_new_trade, is_long, is_short, opened_position, None)

    @classmethod
    def can_close_trade(cls, symbol: str) -> LastTradeStatus:
        last_trade = get_last_time_trade(symbol)
        ready_to_close = last_trade is not None and last_trade.status == TradeStatus.opened.name
        is_long = ready_to_close and last_trade.trend == TradeType.long.name
        is_short = ready_to_close and last_trade.trend == TradeType.short.name
        opened_position = last_trade.opened_position if ready_to_close else 0
        entry_date = last_trade.entry_date if ready_to_close else datetime.today()
        return LastTradeStatus(ready_to_close, is_long, is_short, opened_position, entry_date)

    @staticmethod
    def delete_last_in_progress_trade(symbol):
        last_trade = get_last_time_trade(symbol)
        if last_trade is not None and last_trade.status == TradeStatus.in_progress.name:
            session = apply_session()
            session.delete(last_trade)
            session.commit()
            session.close()

    @staticmethod
    def start_new_trade(symbol: str, strategy_name: str, trend: str, create_date=datetime.now(), open_type="",
                        h4_date=None, trend_position=0):
        last_trade = get_last_time_trade(symbol)
        if last_trade is None or last_trade is not None and last_trade.status == TradeStatus.closed.name:
            session = apply_session()
            session.add(
                Trade(
                    symbol=symbol,
                    strategy=strategy_name,
                    trend=trend,
                    status=TradeStatus.in_progress.name,
                    create_date=create_date,
                    open_type=open_type,
                    h4_date=h4_date,
                    opened_position=trend_position
                )
            )
            session.commit()
            session.close()

    @staticmethod
    def update_open_trade(symbol: str, balance: float, trade_type, position, indicator, indicator_value=0,
                          entry_date=datetime.now()):
        last_trade = get_last_time_trade(symbol)
        session = apply_session()
        if last_trade is None:
            return
        session.delete(last_trade)
        last_trade.entry_signal = trade_type
        last_trade.entry_date = entry_date
        last_trade.status = TradeStatus.opened.name
        last_trade.opened_position = position
        last_trade.quantity = balance / position
        session.add(last_trade)
        session.add(
            Signal(
                symbol=symbol,
                indicator=indicator,
                indicator_value=str(indicator_value),
                trade_signal=trade_type,
                trade_status=TradeStatus.opened.name,
                trade_id=last_trade.id,
            )
        )
        gain = (last_trade.quantity * position + last_trade.quantity * position * 0.3) / last_trade.quantity
        loss = (last_trade.quantity * position - last_trade.quantity * position * 0.15) / last_trade.quantity
        log.info(f"{symbol} take profit {gain} stop loss {loss}")
        new_balance = balance - last_trade.quantity * position
        session.commit()
        session.close()
        return new_balance

    @staticmethod
    def update_close_trade(
            symbol: str,
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
        last_trade = get_last_time_trade(symbol)
        session = apply_session()
        if last_trade is None or last_trade.opened_position is None:
            return

        session.delete(last_trade)
        last_trade.exit_signal = trade_type
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

        # fee = (last_trade.opened_position * (0.061110 / 100) * last_trade.quantity) + (
        #         last_trade.closed_position * (0.061110 / 100) * last_trade.quantity
        # )
        fee = 0
        # print("balance is {}".format(self.balance))
        last_trade.result = result - fee
        # print("close order result {} fee {}".format(result - fee, fee))
        session.add(last_trade)
        session.add(
            Signal(
                symbol=symbol,
                indicator=indicator,
                indicator_value=str(indicator_value),
                trade_signal=trade_type,
                trade_status=TradeStatus.closed.name,
                trade_id=last_trade.id,
            )
        )
        new_balance = last_trade.opened_position * last_trade.quantity + result - fee
        session.commit()
        session.close()
        return new_balance

    @staticmethod
    def get_all_open_trade_signal_indicators(trade_id: str):
        signals = get_open_trade_signals(trade_id)
        return list(map(lambda s: s.indicator, signals))

    @classmethod
    def is_take_profit(cls, symbol: str, candles):
        last_trade = cls.get_trade(symbol)
        if last_trade is not None and last_trade.status == TradeStatus.opened.name:
            low_price = candles.low[-1]
            high_price = candles.high[-1]

            take_profit = get_take_profit(symbol, last_trade.opened_position, last_trade.quantity)

            profit = (high_price - last_trade.opened_position) * last_trade.quantity
            if last_trade.trend == TradeType.short.name:
                profit = (last_trade.opened_position - low_price) * last_trade.quantity

            return profit >= take_profit, take_profit
        return False, 0

    @classmethod
    def is_atr_take_profit(cls, symbol: str, candles):
        last_trade = cls.get_trade(symbol)
        if last_trade is not None and last_trade.status == TradeStatus.opened.name:
            entry_candles = candles[:last_trade.entry_date]
            atr_data = atr(entry_candles.high, entry_candles.low, entry_candles.close)
            atr_times = 5
            profit = (candles.close[-1] - last_trade.opened_position) * atr_times
            if last_trade.trend == TradeType.short.name:
                profit = (last_trade.opened_position - candles.close[-1]) * atr_times

            return profit >= atr_data[-1] * atr_times, atr_data[-1] * atr_times * last_trade.quantity
        return False, 0

    @classmethod
    def is_stop_loss(cls, symbol: str, candles):
        last_trade = cls.get_trade(symbol)
        if last_trade is not None and last_trade.status == TradeStatus.opened.name:
            low_price = candles.low[-1]
            high_price = candles.high[-1]

            stop_loss = get_stop_loss(symbol, last_trade.opened_position, last_trade.quantity)

            loss = (last_trade.opened_position - low_price) * last_trade.quantity
            if last_trade.trend == TradeType.short.name:
                loss = (high_price - last_trade.opened_position) * last_trade.quantity

            return loss >= stop_loss, stop_loss
        return False, 0

    @classmethod
    def is_atr_stop_loss(cls, symbol: str, candles):
        last_trade = cls.get_trade(symbol)
        if last_trade is not None and last_trade.status == TradeStatus.opened.name:
            entry_candles = candles[:last_trade.entry_date]
            atr_data = atr(entry_candles.high, entry_candles.low, entry_candles.close)
            atr_times = 5
            loss = (last_trade.opened_position - candles.close[-1]) * atr_times
            if last_trade.trend == TradeType.short.name:
                loss = (candles.close[-1] - last_trade.opened_position) * atr_times

            return loss >= atr_data[-1] * atr_times, atr_data[-1] * atr_times * last_trade.quantity
        return False, 0
