import asyncio
import logging

from pandas_ta import willr

from konjac2.bot.telegram_bot import say_something
from konjac2.models.trade import TradeStatus, get_last_time_trade
from konjac2.service.fetcher import fetch_data
from konjac2.indicator.utils import TradeType, resample_to_interval
from konjac2.service.forex.place_order import close_trade, has_opened_trades, make_trade
from konjac2.strategy.logistic_regression_strategy import LogisticRegressionStrategy
from . import Instruments
from ..service.crypto.binance import place_trade, close_position
from ..service.crypto.gemini import sell_spot, buy_spot
from ..strategy.abc_strategy import ABCStrategy
from ..strategy.cci_ema_strategy import CCIEMAStrategy
from ..strategy.ema_squeeze_strategy import EmaSqueezeStrategy
from ..strategy.ut_bot_strategy import UTBotStrategy

log = logging.getLogger(__name__)


async def smart_bot(currency="ETH"):
    spot_symbol = f"{currency}/USD"
    future_symbol = f"{currency}/USDT"
    strategy = UTBotStrategy(symbol=spot_symbol)
    data = fetch_data(spot_symbol, "H1", True, limit=1500)
    log.info(f"fetching data for {spot_symbol} {data.index[-1]}")
    d_data = resample_to_interval(data, 360)
    # d_data = fetch_data(query_symbol, "H4", True, counts=1500)

    # opened_position = opened_position_by_symbol(trade_symbol)

    is_exit_trade = strategy.exit_signal(data, d_data)
    trade = get_last_time_trade(spot_symbol)
    if is_exit_trade and trade is not None and trade.status == TradeStatus.closed.name:
        try:
            sell_spot(spot_symbol)
            close_position(future_symbol)
            log.info("closed position!")
            say_something("closed position {}".format(spot_symbol))
        except Exception as err:
            log.error("closed position error! {}".format(err))
            sell_spot(spot_symbol)
            close_position(future_symbol)

    strategy.seek_trend(data, d_data)
    is_opened_trade = strategy.entry_signal(data, d_data)
    trade = get_last_time_trade(spot_symbol)
    if is_opened_trade and trade is not None and trade.status == TradeStatus.opened.name:
        trade_type = TradeType.long if trade.trend == TradeType.long.name else TradeType.short
        try:
            if trade_type == TradeType.long:
                buy_spot(spot_symbol)
            place_trade(future_symbol, "buy", trade_type)
            log.info("opened position!")
            say_something("opened position {}".format(spot_symbol))
        except Exception as err:
            log.error("open position error! {}".format(err))
            if trade_type == TradeType.long:
                buy_spot(spot_symbol)
            place_trade(future_symbol, "buy", trade_type)
            say_something("opened position failed!")
    log.info("job running done!")


async def scan_crypto():
    await smart_bot()


async def trade_forex(symbol="EUR_USD", trading_strategy: type[ABCStrategy] = CCIEMAStrategy, quantity=15000):
    query_symbol = symbol
    trade_symbol = symbol
    strategy = trading_strategy(symbol=query_symbol)
    data = fetch_data(query_symbol, "H1", True, counts=5000)
    # d_data = fetch_data(query_symbol, "H4", True, counts=500)
    d_data = resample_to_interval(data, 360)

    is_exit_trade = strategy.exit_signal(data, day_candles=d_data)
    trade = get_last_time_trade(query_symbol)
    if trade is not None and not has_opened_trades(query_symbol):
        strategy.close_order_by_exchange(data)

    if is_exit_trade and trade is not None and trade.status == TradeStatus.closed.name:
        try:
            close_trade(trade_symbol)
            log.info("closed position!")
            say_something("closed position {}".format(query_symbol))
        except Exception as err:
            log.error("closed position error! {}".format(err))
            close_trade(trade_symbol)

    strategy.seek_trend(data, day_candles=d_data)
    is_opened_trade = strategy.entry_signal(data, day_candles=d_data)
    trade = get_last_time_trade(query_symbol)
    if (
            is_opened_trade
            and trade is not None
            and trade.status == TradeStatus.opened.name
            and not has_opened_trades(query_symbol)
    ):
        try:
            make_trade(trade_symbol, trade.trend, quantity=quantity)
            log.info("opened position!")
            say_something("opened position {}".format(query_symbol))
        except Exception as err:
            log.error("open position error! {}".format(err))
            make_trade(trade_symbol, trade.trend, quantity=quantity)
            say_something("opened position failed!")
    log.info("job running done!")


async def retrieve_fx_position_state(symbol):
    if has_opened_trades(symbol):
        data = fetch_data(symbol, "H1", False, counts=500)
        willr_ = willr(data.high, data.low, data.close)
        if willr_[-1] > -30 or willr_[-1] < -70:
            say_something("{} should consider close {}".format(symbol, willr_[-1]))


async def scan_forex():
    try:
        await trade_forex(symbol="USD_JPY", trading_strategy=EmaSqueezeStrategy, quantity=5000)
    except Exception as err:
        log.error(str(err))

    # await trade_forex(trading_strategy=LogisticRegressionStrategy)
    # await trade_forex(symbol="WTICO_USD", trading_strategy=UTBotStrategy, quantity=80)


async def scanner_job():
    for instrument in Instruments:
        pass
        # await retrieve_fx_position_state(instrument)


async def scanner_h1_job():
    await asyncio.sleep(30)
    await scan_forex()
    await asyncio.sleep(60)
    await scan_crypto()
