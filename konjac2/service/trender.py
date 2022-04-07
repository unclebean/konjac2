from datetime import datetime
from konjac2.models import apply_session
from konjac2.models.trend import TradingTrend


def get_today_trenders():
    session = apply_session()
    today = datetime.now()
    trenders = session.query(TradingTrend).filter(TradingTrend.update_date == today.strftime("%Y-%m-%d")).all()
    session.close()
    return trenders
