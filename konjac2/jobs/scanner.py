import asyncio
import logging
from datetime import datetime as dt
from konjac2.bot.telegram_bot import say_something
from konjac2.models.trade import TradeStatus, get_last_time_trade
from konjac2.service.crypto.fetcher import opened_position_by_symbol, place_trade
from konjac2.service.fetcher import fetch_data
from konjac2.indicator.heikin_ashi_momentum import heikin_ashi_mom
from konjac2.indicator.squeeze_momentum import squeeze
from konjac2.indicator.hurst import hurst
from konjac2.models import apply_session
from konjac2.models.trend import TradingTrend
from konjac2.indicator.utils import TradeType
from konjac2.service.forex.place_order import close_trade, has_opened_trades, make_trade
from konjac2.strategy.bbcci_strategy import BBCCIStrategy
from konjac2.strategy.logistic_regression_strategy import LogisticRegressionStrategy
from . import Instruments, Cryptos
from ..indicator.moving_average import moving_average
from ..service.utils import filter_incomplete_h4_data

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


async def smart_bot(currency="SAND"):
    query_symbol = f"{currency}-PERP"
    trade_symbol = f"{currency}-PERP"
    strategy = BBCCIStrategy(symbol=query_symbol)
    data = fetch_data(query_symbol, "M15", True, limit=1500)
    h6_data = fetch_data(query_symbol, "H4", True, counts=100)
    d_data = fetch_data(query_symbol, "D", True, counts=100)

    h6_data = filter_incomplete_h4_data(h6_data)
    opened_position = opened_position_by_symbol(trade_symbol)

    is_exit_trade = strategy.exit_signal(data, h6_data, d_data)
    trade = get_last_time_trade(query_symbol)
    if is_exit_trade and opened_position is not None and trade is not None and trade.status == TradeStatus.closed.name:
        try:
            place_trade(trade_symbol, "sell")
            log.info("closed position!")
            say_something("closed position {}".format(query_symbol))
        except Exception as err:
            log.error("closed position error! {}".format(err))
            place_trade(trade_symbol, "sell")

    strategy.seek_trend(data, h6_data, d_data)
    is_opened_trade = strategy.entry_signal(data, h6_data, d_data)
    trade = get_last_time_trade(query_symbol)
    if is_opened_trade and opened_position is None and trade is not None and trade.status == TradeStatus.opened.name:
        try:
            place_trade(trade_symbol, "buy", trade.trend)
            log.info("opened position!")
            say_something("opened position {}".format(query_symbol))
        except Exception as err:
            log.error("open position error! {}".format(err))
            place_trade(trade_symbol, "buy", trade.trend)
            say_something("opened position failed!")
    log.info("job running done!")


async def scan_crypto():
    for currency in Cryptos:
        try:
            await smart_bot(currency=currency)
        except Exception as err:
            print(str(err))


async def trade_eur_usd():
    query_symbol = "EUR_USD"
    trade_symbol = "EUR_USD"
    strategy = LogisticRegressionStrategy(symbol=query_symbol)
    data = fetch_data(query_symbol, "H1", True, counts=1000)
    h4_data = fetch_data(query_symbol, "H4", True, counts=1000)

    is_exit_trade = strategy.exit_signal(data)
    trade = get_last_time_trade(query_symbol)
    if is_exit_trade and trade is not None and trade.status == TradeStatus.closed.name:
        try:
            close_trade(trade_symbol)
            log.info("closed position!")
            say_something("closed position {}".format(query_symbol))
        except Exception as err:
            log.error("closed position error! {}".format(err))
            close_trade(trade_symbol)

    strategy.seek_trend(data, h4_data)
    is_opened_trade = strategy.entry_signal(data, h4_data)
    trade = get_last_time_trade(query_symbol)
    if (
        is_opened_trade
        and trade is not None
        and trade.status == TradeStatus.opened.name
        and not has_opened_trades(query_symbol)
    ):
        try:
            make_trade(trade_symbol, trade.trend)
            log.info("opened position!")
            say_something("opened position {}".format(query_symbol))
        except Exception as err:
            log.error("open position error! {}".format(err))
            make_trade(trade_symbol, trade.trend)
            say_something("opened position failed!")
    log.info("job running done!")


async def place_crypto_order(symbol: str, trend: str):
    if symbol is not None and trend is not None:
        data = fetch_data(symbol, "H1", True, counts=100)
        ma = moving_average(data.close)
        place_trade(symbol, "buy", trend, loss_position=ma[-2])


async def scanner_job():
    await asyncio.sleep(30)
    await scan_crypto()
    await trade_eur_usd()
