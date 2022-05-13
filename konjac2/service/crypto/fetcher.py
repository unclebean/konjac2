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
    since = kwargs.get("since", None)
    limit = kwargs.get("limit", None)
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


def buy_spot(symbol, account=""):
    exchange = get_context(account=account)
    available_balance = get_ftx_balance(account=account)

    price = ftx_fetcher(symbol, "M15", complete=False)[-1:]["close"].values[0]
    amount = available_balance / price
    exchange.create_market_order(symbol, "buy", amount)


def sell_spot(symbol, account=""):
    exchanage = get_context(account=account)
    currency_code = symbol.replace("/USD", "")
    amount = get_ftx_balance_bu_currency_code(currency_code, account=account)
    exchanage.create_market_sell_order(symbol, amount)


def place_trade(symbol, side, tradeType="", tp=0, sl=0):
    if side == "buy":
        open_position(symbol, tradeType, tp, sl)
    else:
        close_position(symbol)


def open_position(symbol, tradeType, tp=0, sl=0):
    exchange = get_context()
    balance = get_ftx_balance()
    price = ftx_fetcher(symbol, "M15", complete=False)[-1:]["close"].values[0]
    amount = balance / price * 1
    side = "buy" if tradeType == "long" else "sell"
    exchange.cancel_all_orders(symbol)
    exchange.create_market_order(symbol, side, amount)
    gain_rate = price * 0.03 if tp == 0 else tp
    loss_rate = price * 0.03 if sl == 0 else sl
    if side == "buy":
        gain = price + gain_rate
        loss = price - loss_rate
        exchange.create_order(symbol, "takeProfit", "sell", amount, None, params={"triggerPrice": gain})
        exchange.create_order(symbol, "stop", "sell", amount, None, params={"triggerPrice": loss})
    else:
        gain = price - gain_rate
        loss = price + loss_rate
        exchange.create_order(symbol, "takeProfit", "buy", amount, None, params={"triggerPrice": gain})
        exchange.create_order(symbol, "stop", "buy", amount, None, params={"triggerPrice": loss})


def close_position(symbol):
    exchange = get_context()
    positions = exchange.fetch_positions()
    symbol_position = next(p for p in positions if p["info"]["future"] == symbol)["info"]
    side = symbol_position["side"]
    if side == "buy":
        exchange.create_market_sell_order(symbol, float(symbol_position["openSize"]))
    else:
        exchange.create_market_buy_order(symbol, float(symbol_position["openSize"]))
    exchange.cancel_all_orders(symbol)


def opened_positions():
    exchange = get_context()
    positions = exchange.fetch_positions()
    return list(p for p in positions if p["info"]["size"] != "0.0")


def opened_position_by_symbol(symbol):
    positions = opened_positions()
    position = next((p for p in positions if p["info"]["future"] == symbol), None)
    return position
