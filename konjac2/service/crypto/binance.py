import logging

from konjac2.service.crypto.context import get_context
from konjac2.service.crypto.fetcher import _fetcher

log = logging.getLogger(__name__)


def place_trade(symbol, side, tradeType="", tp=0, sl=0, loss_position=None):
    if side == "buy":
        open_position(symbol, tradeType, tp, sl, loss_position)
    else:
        close_position(symbol)


def open_position(symbol, tradeType, tp=0, sl=0, loss_position=None):
    exchange = get_context()
    balance = _get_binance_balance()
    log.info("open position for {} current balance {}".format(symbol, balance))
    price = _binance_fetcher(symbol, "M15", complete=False)[-1:]["close"].values[0]
    amount = balance / price * 5
    side = "buy" if tradeType == "long" else "sell"
    exchange.cancel_all_orders(symbol)
    exchange.create_market_order(symbol, side, amount)
    quantity_price = amount * price
    gain_rate = 0.08 if tp == 0 else tp
    loss_rate = 0.05 if sl == 0 else sl
    if side == "buy":
        gain = (quantity_price + quantity_price * gain_rate) / amount
        loss = (quantity_price - quantity_price * loss_rate) / amount
        loss_price = loss_position if loss_position is not None else loss
        exchange.create_order(symbol, "takeProfit", "sell", amount, None, params={"triggerPrice": gain})
        exchange.create_order(symbol, "stop", "sell", amount, None, params={"triggerPrice": loss_price})
    else:
        gain = (quantity_price - quantity_price * gain_rate) / amount
        loss = (quantity_price + quantity_price * loss_rate) / amount
        loss_price = loss_position if loss_position is not None else loss
        exchange.create_order(symbol, "takeProfit", "buy", amount, None, params={"triggerPrice": gain})
        exchange.create_order(symbol, "stop", "buy", amount, None, params={"triggerPrice": loss_price})


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


def _get_binance_balance():
    exchange = get_context()
    response = exchange.fetch_balance()
    return response["free"]["USD"]


def _binance_fetcher(symbol, timeframe, complete=True, **kwargs):
    exchange = get_context()
    since = kwargs.get("since", None)
    limit = kwargs.get("limit", None)
    return _fetcher(exchange, symbol, timeframe, complete, since, limit=limit)
