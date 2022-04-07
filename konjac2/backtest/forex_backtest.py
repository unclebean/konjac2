import logging
import pandas as pd
from pandas_ta.volatility import bbands
from sqlalchemy.sql import func

from konjac2.strategy.bbcci_strategy import BBCCIStrategy
from .prepare_data import prepare_forex_backtest_data
from ..indicator.heikin_ashi_momentum import heikin_ashi_mom
from ..indicator.bb_cci_momentum import bb_cci_mom, cci_entry_exit_signal
from ..indicator.utils import TradeType
from ..models import apply_session
from ..models.trade import Trade, TradeStatus, get_last_time_trade

logging.basicConfig()
logging.getLogger("sqlalchemy").setLevel(logging.ERROR)


def fx_trend_backtest(symbol: str):
    # prepare_forex_backtest_data(symbol, "D", step_hours=24)
    # prepare_forex_backtest_data(symbol, "H6", step_hours=6)
    day_data = pd.read_csv(f"{symbol}_24_0.csv", index_col="date", parse_dates=True)
    h6_data = pd.read_csv(f"{symbol}_6_0.csv", index_col="date", parse_dates=True)

    threadholder, volatility = heikin_ashi_mom(day_data, h6_data)
    h6_data["volatility"] = volatility
    h6_data["date"] = h6_data.index

    orders = []
    for i in range(len(h6_data)):
        prev_row = h6_data.iloc[i - 1, :]
        row = h6_data.iloc[i, :]
        thd = threadholder[row.date.replace(hour=9, minute=0)]

        if thd <= abs(prev_row.volatility) and prev_row.volatility > 0:
            orders.append({"trend": "long", "result": row.close > row.open, "profit": row.close - row.open})

        if thd <= abs(prev_row.volatility) and prev_row.volatility < 0:
            orders.append({"trend": "short", "result": row.close < row.open, "profit": row.open - row.close})

    return orders


def fx_short_term_backtest_v2(symbol: str):
    session = apply_session()
    trades = session.query(Trade).filter(Trade.symbol == symbol)
    trades.delete(synchronize_session=False)
    session.commit()
    session.close()
    m5_data = pd.read_csv(f"{symbol}_0_5.csv", index_col="date", parse_dates=True)
    strategy = BBCCIStrategy(symbol=symbol)
    for window in m5_data.rolling(window=144 * 5):
        if len(window.index) < 144 * 5:
            continue
        strategy.seek_trend(window)
        strategy.entry_signal(window)
        strategy.exit_signal(window)
        print(strategy.get_trade())
    session = apply_session()
    total_result = session.query(
        func.sum(Trade.result).label("total_result"),
    ).filter(Trade.symbol == symbol)
    session.close()
    return total_result.scalar()


def fx_short_term_backtest(symbol: str):
    # prepare_forex_backtest_data(symbol, "M5", step_hours=0, step_mins=5)
    m5_data = pd.read_csv(f"{symbol}_0_5.csv", index_col="date", parse_dates=True)
    bb_55 = bbands(m5_data.close, 55)
    m5_data["trend"], _ = bb_cci_mom(m5_data)
    m5_data["signal"], m5_data["cci34"], m5_data["cci144"] = cci_entry_exit_signal(m5_data)
    m5_data["bbl"] = bb_55["BBL_55_2.0"]
    m5_data["bbu"] = bb_55["BBU_55_2.0"]
    m5_data["date"] = m5_data.index
    session = apply_session()
    trades = session.query(Trade).filter(Trade.symbol == symbol)
    trades.delete(synchronize_session=False)
    session.commit()
    session.close()
    for i in range(len(m5_data)):
        pprev_row = m5_data.iloc[i - 2, :]
        prev_row = m5_data.iloc[i - 1, :]
        row = m5_data.iloc[i, :]
        trend = None
        if pprev_row.trend and prev_row.trend and row.trend and row.cci144 > 80:
            trend = TradeType.long.name
        if pprev_row.trend and prev_row.trend and row.trend and row.cci144 < -80:
            trend = TradeType.short.name

        # start trade
        if trend is not None:
            last_trade = get_last_time_trade(symbol)

            if (
                last_trade is not None
                and last_trade.status == TradeStatus.in_progress.name
                and last_trade.trend == trend
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
                        symbol=symbol,
                        strategy="bbcci",
                        trend=trend,
                        status=TradeStatus.in_progress.name,
                        create_date=row.date,
                    )
                )
                session.commit()
                session.close()
                continue
        # open position
        if row.signal:
            last_trade = get_last_time_trade(symbol)
            if (
                last_trade is not None
                and last_trade.status != TradeStatus.closed.name
                and last_trade.status != TradeStatus.opend.name
            ):
                if last_trade.trend == TradeType.long.name and row.cci34 <= -240:
                    session = apply_session()
                    last_trade = (
                        session.query(Trade).filter(Trade.symbol == symbol).order_by(Trade.create_date.desc())
                    ).first()
                    session.delete(last_trade)
                    last_trade.entry_signal = TradeType.long.name
                    last_trade.entry_date = row.date
                    last_trade.status = TradeStatus.opend.name
                    last_trade.opend_position = row.close
                    session.add(last_trade)
                    session.commit()
                    session.close()
                    continue
                if last_trade.trend == TradeType.short.name and row.cci34 >= 240:
                    print(f"open short position {row.cci34} {row.date}")
                    session = apply_session()
                    last_trade = (
                        session.query(Trade).filter(Trade.symbol == symbol).order_by(Trade.create_date.desc())
                    ).first()
                    session.delete(last_trade)
                    last_trade.entry_signal = TradeType.short.name
                    last_trade.entry_date = row.date
                    last_trade.status = TradeStatus.opend.name
                    last_trade.opend_position = row.close
                    session.add(last_trade)
                    session.commit()
                    session.close()
                    continue

        last_trade = get_last_time_trade(symbol)
        if (
            last_trade is not None
            and last_trade.status == TradeStatus.opend.name
            and last_trade.trend == TradeType.long.name
            and row.cci34 >= 160
        ):
            session = apply_session()
            last_trade = (
                session.query(Trade).filter(Trade.symbol == symbol).order_by(Trade.create_date.desc())
            ).first()
            session.delete(last_trade)
            last_trade.exit_signal = TradeType.short.name
            last_trade.exit_date = row.date
            last_trade.status = TradeStatus.closed.name
            last_trade.closed_position = row.close
            last_trade.result = row.close - last_trade.opend_position
            session.add(last_trade)
            session.commit()
            session.close()
            continue
        if (
            last_trade is not None
            and last_trade.status == TradeStatus.opend.name
            and last_trade.trend == TradeType.short.name
            and row.cci34 <= -160
        ):
            session = apply_session()
            last_trade = (
                session.query(Trade).filter(Trade.symbol == symbol).order_by(Trade.create_date.desc())
            ).first()
            session.delete(last_trade)
            last_trade.exit_signal = TradeType.long.name
            last_trade.exit_date = row.date
            last_trade.status = TradeStatus.closed.name
            last_trade.closed_position = row.close
            last_trade.result = last_trade.opend_position - row.close
            session.add(last_trade)
            session.commit()
            session.close()
            continue
    session = apply_session()
    total_result = session.query(
        func.sum(Trade.result).label("total_result"),
    ).filter(Trade.symbol == symbol)
    session.close()
    return total_result
