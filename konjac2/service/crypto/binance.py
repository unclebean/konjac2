import logging

from konjac2.indicator.utils import TradeType
from konjac2.service.crypto.context import get_binance_context
from konjac2.service.crypto.fetcher import _fetcher
from konjac2.service.utils import CP_STOP_LOSS, CP_TAKE_PROFIT, CP_MARGIN

log = logging.getLogger(__name__)


def place_trade(symbol, side, trade_type: TradeType, tp=0, sl=0, loss_position=None):
    if side == "buy":
        open_position(symbol, trade_type, tp, sl, loss_position)
    else:
        close_position(symbol)


def open_position(symbol, trade_type: TradeType, tp=0, sl=0, loss_position=None):
    exchange = get_binance_context()
    balance = _get_binance_balance()
    log.info("open position for {} current balance {}".format(symbol, balance))
    price = _binance_fetcher(symbol, "M15", complete=False)[-1:]["close"].values[0]
    amount = balance / price * CP_MARGIN
    side = "buy" if trade_type == TradeType.long else "sell"
    exchange.cancel_all_orders(symbol)
    exchange.create_market_order(symbol, side, amount)
    quantity_price = amount * price
    gain_rate = CP_TAKE_PROFIT if tp == 0 else tp
    loss_rate = CP_STOP_LOSS if sl == 0 else sl
    if side == "buy":
        gain = (quantity_price + quantity_price * gain_rate) / amount
        loss = (quantity_price - quantity_price * loss_rate) / amount
        loss_price = loss_position if loss_position is not None else loss
        exchange.create_order(symbol, "TAKE_PROFIT", "sell", amount, price=gain, params={"stopPrice": gain})
        exchange.create_order(symbol, "STOP", "sell", amount, price=loss_price, params={"stopPrice": loss_price})
    else:
        gain = (quantity_price - quantity_price * gain_rate) / amount
        loss = (quantity_price + quantity_price * loss_rate) / amount
        loss_price = loss_position if loss_position is not None else loss
        exchange.create_order(symbol, "TAKE_PROFIT", "buy", amount, price=gain, params={"stopPrice": gain})
        exchange.create_order(symbol, "STOP", "buy", amount, price=loss_price, params={"stopPrice": loss_price})


def close_position(symbol):
    exchange = get_binance_context()
    positions = exchange.fetch_positions()
    symbol_position = next(p for p in positions if p["symbol"] == symbol)
    side = symbol_position["side"]
    if side == "buy":
        exchange.create_market_sell_order(symbol, float(symbol_position["contracts"]))
    else:
        exchange.create_market_buy_order(symbol, float(symbol_position["contracts"]))
    exchange.cancel_all_orders(symbol)


def _get_binance_balance():
    exchange = get_binance_context()
    response = exchange.fetch_balance()
    return response["free"]["USDT"]


def _binance_fetcher(symbol, timeframe, complete=True, **kwargs):
    exchange = get_binance_context()
    since = kwargs.get("since", None)
    limit = kwargs.get("limit", None)
    return _fetcher(exchange, symbol, timeframe, complete, since, limit=limit)
