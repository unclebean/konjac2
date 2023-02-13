import logging

from fastapi import APIRouter, Request
from pydantic import BaseModel

from konjac2.indicator.utils import TradeType
from konjac2.service.crypto.binance import close_position, place_trade
from konjac2.service.trender import get_today_trenders

log = logging.getLogger(__name__)
router = APIRouter()

TradingViewIPs = [
    "52.89.214.238",
    "34.212.75.30",
    "54.218.53.128",
    "52.32.178.7"
]


class TradeSignal(BaseModel):
    signal: str
    action: str


@router.get("/trends", tags=["trend"])
async def get_daily_trend():
    daily_trends = get_today_trenders()
    return daily_trends


@router.post("/trading_view/signal/{symbol}", tags=["trend"])
async def receive_trading_view_signal(symbol: str, trade_signal: TradeSignal, request: Request):
    client_host = request.client.host
    log.info(f'symbol: {symbol} signal: {trade_signal.signal} action: {trade_signal.action} ip: {client_host}')
    if client_host in TradingViewIPs:
        future_symbol = f"{symbol}/USDT"
        log.info(f"request from trading view for {future_symbol}")
        if trade_signal.action == "sell":
            try:
                # disable spot trade for now
                close_position(future_symbol)
                log.info("closed position!")
            except Exception as err:
                log.error("closed position error! {}".format(err))
                close_position(future_symbol)
        if trade_signal.action == "buy":
            try:
                # disable spot trade for now
                if trade_signal.signal == TradeType.long.name:
                    place_trade(future_symbol, "buy", TradeType.long)
                    log.info("opened position!")
                if trade_signal.signal == TradeType.short.name:
                    place_trade(future_symbol, "buy", TradeType.short)
                    log.info("opened position!")
            except Exception as err:
                log.error("open position error! {}".format(err))
