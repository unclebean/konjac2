import logging
from konjac2.indicator.utils import TradeType
from konjac2.service.forex.context import get_account, get_context
from konjac2.service.utils import get_fx_take_profit_rate, get_fx_stop_loss_rate

log = logging.getLogger(__name__)


def make_trade(symbol: str, signal: str, quantity=15000, stop_loss=0, take_profit=0):
    log.info(
        f"symbol {symbol} strategy signal {signal}",
    )
    if TradeType.long.name == signal:
        _long_trade(symbol, units=quantity, stop_loss=stop_loss, take_profit=take_profit)
    if TradeType.short.name == signal:
        _short_trade(symbol, units=quantity, stop_loss=stop_loss, take_profit=take_profit)


def _long_trade(symbol: str, units, stop_loss, take_profit):
    t_stop_loss = get_fx_stop_loss_rate(symbol) if stop_loss == 0 else stop_loss
    t_take_profit = get_fx_take_profit_rate(symbol) if take_profit == 0  else take_profit
    response = get_context().order.market(
        get_account(),
        **{
            "type": "MARKET",
            "instrument": symbol,
            "units": units,
            "stopLossOnFill": {"distance": str(round(t_stop_loss, 6))},
            "takeProfitOnFill": {"distance": str(round(t_take_profit, 6))},
        }
    )
    log.info("create long trade %s status %d", symbol, response.status)
    return response.status


def _short_trade(symbol: str, units, stop_loss, take_profit):
    t_stop_loss = get_fx_stop_loss_rate(symbol) if stop_loss == 0 else stop_loss
    t_take_profit = get_fx_take_profit_rate(symbol) if take_profit == 0 else take_profit
    response = get_context().order.market(
        get_account(),
        **{
            "type": "MARKET",
            "instrument": symbol,
            "units": -units,
            "stopLossOnFill": {"distance": str(round(t_stop_loss, 6))},
            "takeProfitOnFill": {"distance": str(round(t_take_profit, 6))},
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
