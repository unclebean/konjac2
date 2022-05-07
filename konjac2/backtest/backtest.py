import logging
import pandas as pd
from sqlalchemy.sql import func

from konjac2.strategy.bbcci_strategy import BBCCIStrategy
from konjac2.strategy.dema_supertrend_strategy import DemaSuperTrendStrategy
from konjac2.strategy.vegas_strategy import VegasStrategy
from konjac2.strategy.logistic_regression_strategy import LogisticRegressionStrategy
from .prepare_data import prepare_forex_backtest_data
from ..indicator.heikin_ashi_momentum import heikin_ashi_mom
from ..models import apply_session
from ..models.trade import Trade

logging.basicConfig()
logging.getLogger("sqlalchemy").setLevel(logging.ERROR)


def fx_trend_backtest(symbol: str):
    prepare_forex_backtest_data(symbol, "D", step_hours=24)
    prepare_forex_backtest_data(symbol, "H6", step_hours=6)
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


def short_term_backtest(symbol: str):
    session = apply_session()
    trades = session.query(Trade)
    trades.delete(synchronize_session=False)
    session.commit()
    session.close()
    m5_data = pd.read_csv(f"{symbol}_0_30.csv", index_col="date", parse_dates=True)
    strategy = LogisticRegressionStrategy(symbol=symbol)
    for window in m5_data.rolling(window=144 * 6):
        if len(window.index) < 144 * 6:
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
