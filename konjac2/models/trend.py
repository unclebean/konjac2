from sqlalchemy import Column, String, Date, Time, PrimaryKeyConstraint
from . import Base, apply_session
from datetime import datetime


class TradingTrend(Base):
    __tablename__ = "trading_trend"
    symbol = Column(String)
    trend_name = Column(String)
    trend = Column(String)
    timeframe = Column(String)
    update_date = Column(Date)
    update_time = Column(Time)

    __table_args__ = (PrimaryKeyConstraint("symbol", "trend_name", "update_date", "update_time"), {})

    def __repr__(self):
        return "<TradingTrend(symbol='%s', trend='%s')>" % (self.symbol, self.trend)


def get_last_time_trend(symbol):
    session = apply_session()
    trend = (
        session.query(TradingTrend).filter(TradingTrend.symbol == symbol).order_by(TradingTrend.update_date.desc())
    ).first()
    session.close()
    return trend


def new_trend(symbol, trend_name, trend):
    session = apply_session()
    current_date = datetime.now()
    session.add(
        TradingTrend(
            symbol=symbol,
            trend_name=trend_name,
            trend=trend,
            update_date=current_date.date(),
            update_time=current_date.time(),
        )
    )
    session.commit()
    session.close()
