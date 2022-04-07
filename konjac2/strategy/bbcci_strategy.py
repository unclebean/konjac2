from datetime import datetime
from pandas_ta.momentum import cci
from ..indicator.utils import TradeType, is_crossing_up, is_crossing_down
from ..indicator.bb_cci_momentum import bb_cci_mom
from ..models import apply_session
from ..models.trade import Trade, TradeStatus, get_last_time_trade
from ..models.signal import Signal


class BBCCIStrategy:
    strategy_name = "bbcci"

    def __init__(self, symbol: str):
        self.symbol = symbol

    def seek_trend(self, candles):
        trends, cci144 = bb_cci_mom(candlestick=candles)
        trend = None
        if is_crossing_up(cci144[-1], 80):
            trend = TradeType.long.name
        if is_crossing_down(cci144[-1], -80):
            trend = TradeType.short.name
        if trend is not None and trends[-3] and trends[-2] and trends[-1]:
            last_trade = get_last_time_trade(self.symbol)
            if (
                last_trade is not None
                and last_trade.status == TradeStatus.in_progress.name
                # and last_trade.trend == trend
            ):
                session = apply_session()
                session.delete(last_trade)
                session.commit()
                session.close()
                last_trade = None

            if last_trade is None or last_trade is not None and last_trade.status == TradeStatus.closed.name:
                session = apply_session()
                session.add(
                    Trade(
                        symbol=self.symbol,
                        strategy=self.strategy_name,
                        trend=trend,
                        status=TradeStatus.in_progress.name,
                        create_date=datetime.now(),
                    )
                )
                session.commit()
                session.close()

    def entry_signal(self, candles):
        last_trade = get_last_time_trade(self.symbol)
        cci34 = cci(candles.high, candles.low, candles.close, 34)
        if (
            last_trade is not None
            and last_trade.status != TradeStatus.closed.name
            and last_trade.status != TradeStatus.opend.name
        ):
            if last_trade.trend == TradeType.long.name and is_crossing_down(cci34[-1], -240):
                self._update_open_trade(TradeType.long.name, candles.close[-1], cci34[-1])
            if last_trade.trend == TradeType.short.name and is_crossing_up(cci34[-1], 240):
                self._update_open_trade(TradeType.short.name, candles.close[-1], cci34[-1])

    def exit_signal(self, candles):
        last_trade = get_last_time_trade(self.symbol)
        cci34 = cci(candles.high, candles.low, candles.close, 34)
        if (
            last_trade is not None
            and last_trade.status == TradeStatus.opend.name
            and last_trade.trend == TradeType.long.name
            and cci34[-1] >= 160
        ):
            self._update_close_trade(TradeType.short.name, candles.close[-1], cci34[-1])
        if (
            last_trade is not None
            and last_trade.status == TradeStatus.opend.name
            and last_trade.trend == TradeType.short.name
            and cci34[-1] <= -160
        ):
            self._update_close_trade(TradeType.long.name, candles.close[-1], cci34[-1])

    def get_trade(self):
        return get_last_time_trade(self.symbol)

    def _update_open_trade(self, tradeType, position, indicator_value=0):
        session = apply_session()
        last_trade = (
            session.query(Trade).filter(Trade.symbol == self.symbol).order_by(Trade.create_date.desc())
        ).first()
        session.delete(last_trade)
        last_trade.entry_signal = tradeType
        last_trade.entry_date = datetime.now()
        last_trade.status = TradeStatus.opend.name
        last_trade.opend_position = position
        session.add(last_trade)
        session.add(
            Signal(
                symbol=self.symbol,
                indicator="cci34_240",
                indicator_value=indicator_value,
                trade_signal=tradeType,
                trade_status=TradeStatus.opend.name,
                trade_id=last_trade.id,
            )
        )
        session.commit()
        session.close()

    def _update_close_trade(self, tradeType, position, indicator_value=0):
        session = apply_session()
        last_trade = (
            session.query(Trade).filter(Trade.symbol == self.symbol).order_by(Trade.create_date.desc())
        ).first()
        result = (
            position - last_trade.opend_position
            if tradeType == TradeType.short.name
            else last_trade.opend_position - position
        )
        session.delete(last_trade)
        last_trade.exit_signal = tradeType
        last_trade.exit_date = datetime.now()
        last_trade.status = TradeStatus.closed.name
        last_trade.closed_position = position
        last_trade.result = result
        session.add(last_trade)
        session.add(
            Signal(
                symbol=self.symbol,
                indicator="cci34_160",
                indicator_value=indicator_value,
                trade_signal=tradeType,
                trade_status=TradeStatus.closed.name,
                trade_id=last_trade.id,
            )
        )
        session.commit()
        session.close()
