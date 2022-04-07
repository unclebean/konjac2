import uuid
from enum import Enum
from sqlalchemy import Column, String, DateTime, Float, Index
from sqlalchemy.orm import relationship
from . import Base, apply_session


def generate_uuid():
    return str(uuid.uuid4())


class TradeStatus(Enum):
    pending_by_signal = 0
    opend = 1
    in_progress = 2
    closed = 3


class Trade(Base):
    __tablename__ = "trade"
    id = Column(String, name="id", primary_key=True, default=generate_uuid)
    symbol = Column(String)
    strategy = Column(String)
    trend = Column(String)
    entry_signal = Column(String, nullable=True)
    entry_date = Column(DateTime, nullable=True)
    opend_position = Column(Float, nullable=True)
    exit_signal = Column(String, nullable=True)
    exit_date = Column(DateTime, nullable=True)
    closed_position = Column(Float, nullable=True)
    result = Column(Float, nullable=True)
    status = Column(String)
    create_date = Column(DateTime)
    signals = relationship("Signal")

    Index('symbol', 'strategy', 'create_date')

    # __table_args__ = (PrimaryKeyConstraint("id, symbol", "strategy", "create_date"), {})

    def __repr__(self):
        return "<Trade(symbol='%s', strategy='%s' trend='%s', status='%s')>" % (
            self.symbol,
            self.strategy,
            self.trend,
            self.status
        )


def get_last_time_trade(symbol):
    session = apply_session()
    trade = (session.query(Trade).filter(Trade.symbol == symbol).order_by(Trade.create_date.desc())).first()
    session.close()
    return trade
