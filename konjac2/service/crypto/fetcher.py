import pandas as pd
from datetime import datetime
from .context import get_context, get_binance_context

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
}


def crypto_fetcher(symbol, timeframe, complete=True, **kwargs):
    since = kwargs.get('since', None)
    limit = kwargs.get('limit', None)
    exchange = get_binance_context()
    return _fetcher(exchange, symbol, timeframe, complete, since, limit=limit)


def get_markets():
    exchange = get_context()
    return exchange.load_markets()


def ftx_fetch_pairs():
    exchange = get_context()
    exchange.load_markets()
    return exchange.symbols


def ftx_fetcher(symbol, timerframe, complete=True, since=None):
    exchange = get_context()
    return _fetcher(exchange, symbol, timerframe, complete, since)


def ftx_fetch_balance(symbol="USD"):
    exchange = get_context()
    balance = exchange.fetch_balance()
    total_balance = balance.get("total", {"total": {"USD": 0}})
    return total_balance.get(symbol, 0)


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


def get_ftx_balance(account=""):
    exchange = get_context(account=account)
    response = exchange.fetch_balance()
    return response["free"]["USD"]


def get_ftx_balance_bu_currency_code(currency_code, account=""):
    exchange = get_context(account=account)
    response = exchange.fetch_balance()
    return response.get(currency_code, {"free": 0.0})["free"]


def have_ftx_free_balance(currency_code):
    exchange = get_context()
    response = exchange.fetch_balance()
    balance = response.get(currency_code, {"free": 0.0})["free"]
    return balance != 0.0
