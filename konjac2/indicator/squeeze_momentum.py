import pandas as pd
import pandas_ta as ta

from konjac2.indicator.atr_kc import atr_kc


def squeeze(candlestick):
    # kcdf = ta.kc(candlestick.high, candlestick.low, candlestick.close, length=20, scalar=1.5, mamode="sma", tr=True)
    bbandsdf = ta.bbands(candlestick.close, length=20, std=2, mamode="sma")
    momdf = ta.mom(candlestick.close, length=12)

    upperKC, lowerKC = atr_kc(candlestick)

    high_low = pd.DataFrame([candlestick.high.rolling(20).max(), candlestick.low.rolling(20).min()]).mean()
    sma_close = ta.sma(candlestick.close, length=20)
    high_low_sma_close = pd.DataFrame([high_low, sma_close]).mean()
    # lowerKC = kcdf["KCLs_20_1.5"].round(4)
    # upperKC = kcdf["KCUs_20_1.5"].round(4)
    lowerBB = bbandsdf["BBL_20_2.0"].round(4)
    upperBB = bbandsdf["BBU_20_2.0"].round(4)
    # sqzOn = (lowerBB > lowerKC) & (upperBB < upperKC)
    sqzOff = (lowerBB < lowerKC) & (upperKC < upperBB)
    trends = ta.linreg(candlestick.close - high_low_sma_close, length=20)
    return trends, sqzOff, momdf


def is_squeeze(candlestick):
    _, sqzOff, _ = squeeze(candlestick)
    return not sqzOff[-1]
