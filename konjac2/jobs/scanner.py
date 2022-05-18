import logging
from datetime import datetime as dt
from pandas_ta.volatility import atr
from konjac2.models.trade import TradeStatus, get_last_time_trade
from konjac2.service.crypto.fetcher import opened_position_by_symbol, place_trade
from konjac2.service.fetcher import fetch_data
from konjac2.indicator.heikin_ashi_momentum import heikin_ashi_mom
from konjac2.indicator.squeeze_momentum import squeeze
from konjac2.indicator.hurst import hurst
from konjac2.models import apply_session
from konjac2.models.trend import TradingTrend
from konjac2.indicator.utils import TradeType
from konjac2.strategy.bbcci_strategy import BBCCIStrategy
from konjac2.strategy.logistic_regression_strategy import LogisticRegressionStrategy
from . import TrustCrypto, Instruments, Cryptos


log = logging.getLogger(__name__)


def forex_scanner():
    session = apply_session()
    for symbol in Instruments:
        day_data = fetch_data(symbol, "D", False)
        h6_data = fetch_data(symbol, "H6", False)
        m30_data = fetch_data(symbol, "M30", False)

        trends, is_sqz_off, mom = squeeze(m30_data)
        is_sqz = not is_sqz_off[-1]
        hurst_result = hurst(m30_data.close.values)
        print(f"hurst {hurst_result}")

        order_action = None
        if trends[-1] > 0 and mom[-1] > 0 and hurst_result > 0.5 and is_sqz is not True:
            order_action = TradeType.long.name
        if trends[-1] < 0 and mom[-1] < 0 and hurst_result > 0.5 and is_sqz is not True:
            order_action = TradeType.short.name

        threadholder, short_term_volatility = heikin_ashi_mom(day_data, h6_data)

        trend_action = None
        if threadholder[-1] <= abs(short_term_volatility[-1]) and short_term_volatility[-1] > 0:
            trend_action = TradeType.long.name

        if threadholder[-1] <= abs(short_term_volatility[-1]) and short_term_volatility[-1] < 0:
            trend_action = TradeType.short.name

        now = dt.now()

        if trend_action is not None:
            trend = TradingTrend(
                symbol=symbol,
                trend=trend_action,
                trend_anme="heikin_ashi",
                timeframe="D/H6",
                update_date=now.date(),
                update_time=now.time(),
            )
            session.add(trend)

        print(f"trend {trend_action} order {order_action}")
    session.commit()
    session.close()


async def bbcci_scanner():
    for symbol in Instruments:
        strategy = BBCCIStrategy(symbol=symbol)
        m5_data = fetch_data(symbol, "M5", True)
        strategy.seek_trend(m5_data)
        strategy.entry_signal(m5_data)
        strategy.exit_signal(m5_data)

    for symbol in Cryptos:
        strategy = BBCCIStrategy(symbol=symbol)
        m5_data = fetch_data(symbol, "M5", True, limit=1500)
        strategy.seek_trend(m5_data)
        strategy.entry_signal(m5_data)
        strategy.exit_signal(m5_data)


async def smart_bot():
    query_symbol = "DOGE/USDT"
    trade_symbol = "DOGE-PERP"
    strategy = LogisticRegressionStrategy(symbol=query_symbol)
    data = fetch_data(query_symbol, "H1", True, limit=1500)
    opened_position = opened_position_by_symbol(trade_symbol)

    is_exit_trade = strategy.exit_signal(data)
    trade = get_last_time_trade(query_symbol)
    if is_exit_trade and opened_position is not None and trade is not None and trade.status == TradeStatus.closed.name:
        place_trade(trade_symbol, "sell")

    strategy.seek_trend(data)
    is_opened_trade = strategy.entry_signal(data)
    trade = get_last_time_trade(query_symbol)
    if is_opened_trade and opened_position is None and trade is not None and trade.status == TradeStatus.opened.name:
        atr_value = atr(data.high, data.low, data.close)[-1]
        place_trade(trade_symbol, "buy", trade.trend, tp=atr_value * 3.2, sl=atr_value * 3)

    log.info("job running done!")


async def scan_crypto():
    for crypto in TrustCrypto:
        strategy = LogisticRegressionStrategy(symbol=crypto)
        data = fetch_data(crypto, "H1", True, limit=1500)
        strategy.exit_signal(data)
        strategy.seek_trend(data)
        strategy.entry_signal(data)


async def scan_fx():
    for fx in ["EUR_USD"]:
        strategy = LogisticRegressionStrategy(symbol=fx)
        data = fetch_data(fx, "M30", True, limit=1500)
        strategy.exit_signal(data)
        strategy.seek_trend(data)
        strategy.entry_signal(data)