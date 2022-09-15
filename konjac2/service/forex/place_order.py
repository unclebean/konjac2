import logging
from konjac2.indicator.utils import TradeType
from konjac2.service.forex.context import get_account, get_context

log = logging.getLogger(__name__)

STOP_LOSS = "0.005"
JPY_STOP_LOSS = "0.5"
TAKE_PROFIT = "0.008"


def make_trade(symbol: str, signal: str):
    log.info(
        f"symbol {symbol} strategy signal {signal}",
    )
    if TradeType.long.name == signal:
        _long_trade(symbol)
    if TradeType.short.name == signal:
        _short_trade(symbol)


def _long_trade(symbol: str, units=10000):
    response = get_context().order.market(
        get_account(),
        **{
            "type": "MARKET",
            "instrument": symbol,
            "units": units,
            "stopLossOnFill": {"distance": _get_stop_loss(symbol)},
        }
    )
    log.info("create long trade %s status %d", symbol, response.status)
    return response.status


def _short_trade(symbol: str, units=10000):
    response = get_context().order.market(
        get_account(),
        **{
            "type": "MARKET",
            "instrument": symbol,
            "units": -units,
            "stopLossOnFill": {"distance": _get_stop_loss(symbol)},
        }
    )
    log.info("create short trade %s status %d", symbol, response.status)
    return response.status


def _get_opened_trades():
    response = get_context().trade.list_open(get_account())
    return response.get("trades", 200)


def has_opened_trades(symbol: str):
    trades = _get_opened_trades()
    for trade in trades:
        if trade.instrument == symbol:
            return True
    return False


def close_trade(symbol: str):
    trades = _get_opened_trades()
    for trade in trades:
        if trade.instrument == symbol:
            log.info("closed trade %s, order %s", symbol, trade.id)
            response = get_context().trade.close(get_account(), trade.id)
            log.info("close trade status %d", response.status)


def is_opened_maximum_positions() -> bool:
    try:
        opened_trades = _get_opened_trades()
        log.info(f"opened positions {len(opened_trades)}")
        return len(opened_trades) > 2
    except Exception as err:
        log.error(str(err))
        return False


def _get_stop_loss(symbol: str):
    if "JPY" in symbol:
        return JPY_STOP_LOSS
    return STOP_LOSS
