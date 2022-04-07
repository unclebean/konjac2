from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine("sqlite:///db/konjac2.db", echo=False)

Base = declarative_base()


def apply_session():
    session = sessionmaker(bind=engine)
    return session()


from .trend import TradingTrend
from .trade import Trade
from .signal import Signal


__all__ = ["Base", "TradingTrend", "Trade", "Signal"]
