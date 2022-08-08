import logging
from typing import Optional
from fastapi import APIRouter
from pandas_ta.momentum import macd
from pandas_ta.overlap import ichimoku

from konjac2.indicator.heikin_ashi_momentum import heikin_ashi_mom
from konjac2.indicator.normalized_macd import n_macd
from konjac2.service.fetcher import fetch_data

log = logging.getLogger(__name__)
start_index = -120
router = APIRouter()


@router.get("/chart/{timeframe}/{symbol}", tags=["chart"])
async def fetch_h1(timeframe: str, symbol: str, endDate: Optional[str] = None):
    log.info("fetch for symbol: " + symbol)
    data = fetch_data(symbol, timeframe=timeframe, complete=False)
    h1_data = fetch_data(symbol, timeframe="H1", complete=False)
    h4_data = fetch_data(symbol, timeframe="H4", complete=False)
    return prepare_candles_and_ta(data, endDate, h1_data, h4_data)


def prepare_candles_and_ta(data, hasEndDate=None, h1_data=None, h4_data=None):
    candles = data[start_index:]
    macd_signal, macd_macd, macd_histogram = n_macd(data.close, 13, 21)

    ichimoku_df, _ = ichimoku(data.high, data.low, data.close)
    senkou_a = ichimoku_df["ISA_9"]
    senkou_b = ichimoku_df["ISB_26"]
    tenkan_sen = ichimoku_df["ITS_9"]
    kijun_sen = ichimoku_df["IKS_26"]
    chikou_span = ichimoku_df["ICS_26"]
    threadholder, short_term_volatility = heikin_ashi_mom(h4_data, h1_data, rolling=42, holder_dev=21)

    resp = {
        "marketData": {
            "x": candles.index.values.tolist(),
            "high": candles.high.values.tolist(),
            "low": candles.low.values.tolist(),
            "open": candles.open.values.tolist(),
            "close": candles.close.values.tolist(),
        },
        "macd": {
            "macd": macd_macd[start_index:],
            "signal": macd_signal[start_index:],
            "hist": macd_histogram[start_index:],
        },
        "ichimoku": {
            "tenkan": tenkan_sen[start_index:].tolist(),
            "kijun": kijun_sen[start_index:].tolist(),
            "senkou_a": senkou_a[start_index:].tolist(),
            "senkou_b": senkou_b[start_index:].tolist(),
            # "chikou": chikou_span[start_index:].tolist(),
        },
        "threadholder": threadholder[start_index:].tolist(),
        "volatility": short_term_volatility[start_index:].tolist()
    }
    return resp
