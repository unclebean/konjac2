from konjac2.service.crypto.context import get_gemini_context
from konjac2.service.crypto.fetcher import _fetcher


def gemini_fetcher(symbol, timerframe, complete=True, since=None):
    exchange = get_gemini_context()
    return _fetcher(exchange, symbol, timerframe, complete, since)


def get_gemini_balance():
    exchange = get_gemini_context()
    response = exchange.fetch_balance()
    return response["free"]["USD"]


def get_gemini_balance_bu_currency_code(currency_code):
    exchange = get_gemini_context()
    response = exchange.fetch_balance()
    return response.get(currency_code, {"free": 0.0})["free"]


def buy_spot(symbol):
    exchange = get_gemini_context()
    available_balance = get_gemini_balance()

    price = gemini_fetcher(symbol, "M15", complete=False)[-1:]["close"].values[0]
    amount = available_balance / price * 0.9
    exchange.create_limit_buy_order(symbol, amount, price)


def sell_spot(symbol):
    exchange = get_gemini_context()
    currency_code = symbol.replace("/USD", "")
    price = gemini_fetcher(symbol, "M15", complete=False)[-1:]["close"].values[0]
    amount = get_gemini_balance_bu_currency_code(currency_code)
    exchange.create_limit_sell_order(symbol, amount, price)
