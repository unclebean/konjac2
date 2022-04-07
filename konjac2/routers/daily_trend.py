from fastapi import APIRouter
from konjac2.service.trender import get_today_trenders

router = APIRouter()


@router.get("/trends", tags=["trend"])
async def get_daily_trend():
    daily_trends = get_today_trenders()
    return daily_trends
