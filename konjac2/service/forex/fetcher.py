import pandas as pd
from datetime import datetime as dt
from .context import get_context


def forex_fetcher(
    symbol, timeframe="H1", complete=True, *args 
):
    more_args = args[0]
    counts = more_args.get("counts", None)
    till_date = more_args.get("till_date", None)
    if not till_date:
        candles = _fetch_data(symbol, timeframe, counts)
    else:
        candles = _fetch_data_till(symbol, timeframe, counts, till_date)
    return _create_data_frame(candles, complete)


def _fetch_data(symbol, granularity, count):
    response = get_context().instrument.candles(
        symbol, count=count, granularity=granularity
    )
    candles = response.get("candles", 200)
    return candles


def _fetch_data_till(symbol, granularity, count, till_date):
    response = get_context().instrument.candles(
        symbol,
        count=count,
        granularity=granularity,
        toTime=till_date,
        alignmentTimezone="Asia/Singapore",
    )
    candles = response.get("candles", 200)
    return candles


def _create_data_frame(candles, completeOnly):
    values = []
    for candle in candles:
        time = dt.strptime(candle.time.replace(".000000000Z", ""), "%Y-%m-%dT%H:%M:%S")
        volume = candle.volume
        mid = candle.mid
        if completeOnly and candle.complete:
            values.append([time, mid.o, mid.h, mid.l, mid.c, volume])
        if completeOnly is False:
            values.append([time, mid.o, mid.h, mid.l, mid.c, volume])

    data_frame = pd.DataFrame(
        values, columns=["date", "open", "high", "low", "close", "volume"]
    )
    data_frame.set_index("date", inplace=True)
    return data_frame
