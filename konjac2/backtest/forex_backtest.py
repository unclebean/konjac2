import pandas as pd
from .prepare_data import prepare_forex_backtest_data
from ..indicator.heikin_ashi_momentum import heikin_ashi_mom


def fx_backtest(symbol: str):
    prepare_forex_backtest_data(symbol, "D", step_hours=24)
    prepare_forex_backtest_data(symbol, "H6", step_hours=6)
    day_data = pd.read_csv(f"{symbol}_24_0.csv", index_col="date", parse_dates=True)
    h6_data = pd.read_csv(f"{symbol}_6_0.csv", index_col="date", parse_dates=True)

    threadholder, volatility = heikin_ashi_mom(day_data, h6_data)
    h6_data["volatility"] = volatility
    h6_data['date'] = h6_data.index

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
