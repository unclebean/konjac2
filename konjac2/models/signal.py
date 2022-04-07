from sqlalchemy import Column, String, Index, ForeignKey, PrimaryKeyConstraint
from . import Base


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
