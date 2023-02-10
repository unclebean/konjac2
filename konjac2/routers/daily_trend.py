import logging

from fastapi import APIRouter
from pydantic import BaseModel

from konjac2.service.trender import get_today_trenders

log = logging.getLogger(__name__)
router = APIRouter()

class TradeSignal(BaseModel):
    symbol: str
    signal: str
    action: str


@router.get("/trends", tags=["trend"])
async def get_daily_trend():
    daily_trends = get_today_trenders()
    return daily_trends


@router.post("/trading_view/signal", tags=["trend"])
async def receive_trading_view_signal(trade_signal: TradeSignal):
    log.info(f'symbol: {trade_signal.symbol} signal: {trade_signal.signal} action: {trade_signal.action}')
