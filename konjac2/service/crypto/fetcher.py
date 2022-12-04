import logging
import pandas as pd
from datetime import datetime
from .context import get_binance_context, get_gemini_context

log = logging.getLogger(__name__)

TIMEFRAME_CCXT_MAPPER = {
    "S15": "15s",
    "M1": "1m",
    "M5": "5m",
    "M15": "15m",
    "M30": "30m",
    "H1": "1h",
    "H2": "2h",
    "H4": "4h",
    "H6": "6h",
    "H8": "8h",
    "D": "1d",
    "3D": "3d",
}


def crypto_fetcher(symbol, timeframe, complete=True, **kwargs):
    since = kwargs.get("since", None)
    limit = kwargs.get("limit", None)
    exchange = get_gemini_context()
    # exchange = get_context()
    return _fetcher(exchange, symbol, timeframe, complete, since, limit=limit)


def binance_fetch_pairs():
    exchange = get_binance_context()
    exchange.load_markets()
    return exchange.symbols


def _fetcher(exchange, symbol, timerframe, complete=True, since=None, limit=1500):
    tf = TIMEFRAME_CCXT_MAPPER.get(timerframe, "1h")
    data = exchange.fetch_ohlcv(symbol=symbol, timeframe=tf, since=since, limit=limit)
    dataframe = pd.DataFrame(data, columns=["datetime", "open", "high", "low", "close", "volume"])
    dataframe.set_index("datetime", inplace=True)
    dataframe.index.names = ["date"]
    dataframe.volume = dataframe.volume.map(lambda v: round(v, 4))
    dataframe.index = dataframe.index.map(lambda t: datetime.utcfromtimestamp(t / 1000))
    if complete:
        return dataframe[:-1]
    return dataframe
