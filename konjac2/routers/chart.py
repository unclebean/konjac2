import logging
from typing import Optional
from fastapi import APIRouter
from pandas_ta.momentum import macd
from pandas_ta.overlap import ichimoku

from konjac2.service.fetcher import fetch_data

log = logging.getLogger(__name__)
start_index = -120
router = APIRouter()


@router.get("/chart/{timeframe}/{symbol}", tags=["chart"])
async def fetch_h1(timeframe: str, symbol: str, endDate: Optional[str] = None):
    log.info("fetch for symbol: " + symbol)
    data = fetch_data(symbol, timeframe=timeframe, complete=False)
    return prepare_candles_and_ta(data, endDate)


def prepare_candles_and_ta(data, hasEndDate=None):
    candles = data[start_index:]
    macd_data = macd(data.close, 13, 34)
    macd_macd = macd_data["MACD_13_34_9"]
    macd_histogram = macd_data["MACDh_13_34_9"]
    macd_signal = macd_data["MACDs_13_34_9"]

    ichimoku_df, _ = ichimoku(data.high, data.low, data.close)
    senkou_a = ichimoku_df["ISA_9"]
    senkou_b = ichimoku_df["ISB_26"]
    tenkan_sen = ichimoku_df["ITS_9"]
    kijun_sen = ichimoku_df["IKS_26"]
    chikou_span = ichimoku_df["ICS_26"]

    resp = {
        "marketData": {
            "x": candles.index.values.tolist(),
            "high": candles.high.values.tolist(),
            "low": candles.low.values.tolist(),
            "open": candles.open.values.tolist(),
            "close": candles.close.values.tolist(),
        },
        "macd": {
            "macd": macd_macd[start_index:].tolist(),
            "signal": macd_signal[start_index:].tolist(),
            "hist": macd_histogram[start_index:].tolist(),
        },
        "ichimoku": {
            "tenkan": tenkan_sen[start_index:].tolist(),
            "kijun": kijun_sen[start_index:].tolist(),
            "senkou_a": senkou_a[start_index:].tolist(),
            "senkou_b": senkou_b[start_index:].tolist(),
            # "chikou": chikou_span[start_index:].tolist(),
        },
    }
    return resp
