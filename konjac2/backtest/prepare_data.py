import pandas as pd
from datetime import datetime, timedelta
from ..service.fetcher import fetch_data


def generate_dates(start_date="2019-05-01T21:00:00", step_hours=1, step_mins=0):
    start = datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%S")
    forward_dates = []
    while len(forward_dates) < 150:
        start = start + timedelta(hours=step_hours, minutes=step_mins)
        # if start.weekday() < 5:
        forward_dates.append(start)

    # return np.random.choice(forward_dates, 100, replace=False)
    return forward_dates


def prepare_forex_backtest_data(symbol: str, timeframe: str, step_hours=1, step_mins=0):
    dates = generate_dates(start_date="2021-12-01T00:00:00", step_hours=step_hours, step_mins=step_mins)
    datasets = None
    for date in dates:
        predict_date = date.strftime("%Y-%m-%dT%H:%M:%S")
        m30 = fetch_data(symbol, timeframe, True, counts=5000, till_date=predict_date)
        datasets = m30 if datasets is None else pd.concat([datasets, m30], axis=0)
    datasets = datasets.reset_index().drop_duplicates(subset="date", keep="first").set_index("date")
    datasets.to_csv(f"{symbol}_{step_hours}_{step_mins}.csv")
    return datasets
