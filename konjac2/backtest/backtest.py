import logging
from datetime import timedelta
import pandas as pd
from sqlalchemy.sql import func

from konjac2.strategy.bbcci_strategy import BBCCIStrategy
from konjac2.strategy.dema_supertrend_strategy import DemaSuperTrendStrategy
from konjac2.strategy.macd_histogram_strategy import MacdHistogramStrategy
from konjac2.strategy.vegas_strategy import VegasStrategy
from konjac2.strategy.logistic_regression_strategy import LogisticRegressionStrategy
from .prepare_data import prepare_forex_backtest_data
from ..indicator.heikin_ashi_momentum import heikin_ashi_mom
from ..indicator.utils import resample_to_interval
from ..models import apply_session
from ..models.trade import Trade
from ..strategy.bb_stoch_strategy import BBStochStrategy
from ..strategy.cci_histogram_strategy import CCIHistogramStrategy
from ..strategy.ce_rsi_strategy import CERSIStrategy
from ..strategy.ema_stoch_rsi_strategy import EmaStochRsiStrategy
from ..strategy.ichimoku_willr_strategy import IchimokuWillR
from ..strategy.macd_rsi_strategy import MacdRsiStrategy
from ..strategy.macd_rsi_vwap_strategy import MacdRsiVwapStrategy
from ..strategy.n_macd_volatility_strategy import NMacdVolatilityStrategy
from ..strategy.smoothed_ha_strategy import SmoothedHAStrategy
from ..strategy.strategy_five import StrategyFive
from ..strategy.strategy_one import StrategyOne
from ..strategy.vix_strategy import VixStrategy
from ..strategy.vwap_rsi_strategy import VwapRsiStrategy
from ..strategy.vwap_rsi_willr_strategy import VwapRsiWillR

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
    h1_data = pd.read_csv(f"{symbol}_0_5.csv", index_col="date", parse_dates=True).loc["2019-08-01 00:00:00":]
    strategy = BBCCIStrategy(symbol=symbol)
    for window in h1_data.rolling(window=999):
        if len(window.index) < 999:
            continue

        current_day_data = resample_to_interval(window, 60)
        strategy.exit_signal(window, current_day_data)
        strategy.seek_trend(window, current_day_data)
        strategy.entry_signal(window, current_day_data)
        print(strategy.get_trade())
    session = apply_session()
    total_result = session.query(
        func.sum(Trade.result).label("total_result"),
    ).filter(Trade.symbol == symbol)
    session.close()
    print(strategy.balance)
    return total_result.scalar()


def test(symbol: str):
    m5_data = pd.read_csv(f"{symbol}_1_0.csv", index_col="date", parse_dates=True)
    return m5_data.loc["2021-11-20 00:00:00":]


def fx_short_term_backtest(symbol: str):
    session = apply_session()
    trades = session.query(Trade)
    trades.delete(synchronize_session=False)
    session.commit()
    session.close()
    m5_data = pd.read_csv(f"{symbol}_1_0.csv", index_col="date", parse_dates=True) #.loc["2022-03-20 00:00:00":]
    h4_data = pd.read_csv(f"{symbol}_4_0.csv", index_col="date", parse_dates=True)
    strategy = IchimokuWillR(symbol=symbol)
    for window in m5_data.rolling(window=999):
        if len(window.index) < 999:
            continue
        # last_day = window.index[-1].strftime("%Y-%m-%d")
        last_index = window.index[-1]
        if 5 <= last_index.hour < 9:
            last_h4_index = last_index.strftime("%Y-%m-%d") + " 01:00:00"
        elif 9 <= last_index.hour < 13:
            last_h4_index = last_index.strftime("%Y-%m-%d") + " 05:00:00"
        elif 13 <= last_index.hour < 17:
            last_h4_index = last_index.strftime("%Y-%m-%d") + " 09:00:00"
        elif 17 <= last_index.hour < 21:
            last_h4_index = last_index.strftime("%Y-%m-%d") + " 13:00:00"
        elif 21 <= last_index.hour <= 23:
            last_h4_index = last_index.strftime("%Y-%m-%d") + " 17:00:00"
        else:
            last_h4_index = (last_index - timedelta(days=1)).strftime("%Y-%m-%d") + " 21:00:00"

        print(f">>>>>> H1: {last_index} H4: {last_h4_index}")

        # print(window)
        current_day_data = h4_data.loc[:last_h4_index]
        # print(current_day_data)
        strategy.exit_signal(window)
        strategy.seek_trend(window, current_day_data)
        strategy.entry_signal(window, current_day_data)
        print(strategy.get_trade())
    session = apply_session()
    total_result = session.query(
        func.sum(Trade.result).label("total_result"),
    ).filter(Trade.symbol == symbol)
    session.close()
    print(strategy.balance)
    return total_result.scalar()


def zt(window):
    print(window)
    return window
