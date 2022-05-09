from sqlalchemy import Column, String, Index, ForeignKey, PrimaryKeyConstraint

from .trade import TradeStatus
from . import Base, apply_session


class Signal(Base):
    __tablename__ = "signal"
    symbol = Column(String)
    indicator = Column(String)
    indicator_value = Column(String)
    trade_signal = Column(String)
    trade_status = Column(String)
    trade_id = Column(String, ForeignKey("trade.id"), index=True)

    __table_args__ = (PrimaryKeyConstraint("symbol", "indicator", "trade_status", "trade_id"), {})
    Index("symbol", "indicator", "trade_status", "trade_id", unique=True)


def get_open_trade_signals(trade_id: str):
    session = apply_session()
    signals = session.query(Signal).filter(Signal.trade_id == trade_id, Signal.trade_status == TradeStatus.opened.name)
    session.close()
    return signals
