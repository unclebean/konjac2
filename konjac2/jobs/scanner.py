import asyncio
import logging

from pandas_ta import willr, atr

from konjac2.bot.telegram_bot import say_something
from konjac2.models.trade import TradeStatus, get_last_time_trade
from konjac2.service.fetcher import fetch_data
from konjac2.indicator.utils import TradeType, resample_to_interval
from konjac2.service.forex.place_order import close_trade, has_opened_trades, make_trade
from . import Instruments
from ..service.crypto.binance import place_trade, close_position
from ..service.crypto.fetcher import binance_fetcher
from ..service.crypto.gemini import sell_spot, buy_spot
from ..strategy.abc_strategy import ABCStrategy
from ..strategy.bb_adx_rsi_strategy import BBAdxRsi
from ..strategy.bb_adx_rsi_strategy_v2 import BBAdxRsiV2
from ..strategy.bbcci_strategy import BBCCIStrategy
from ..strategy.cci_ema_strategy import CCIEMAStrategy
from ..strategy.ema_squeeze_strategy import EmaSqueezeStrategy
from ..strategy.logistic_regression_strategy import LogisticRegressionStrategy
from ..strategy.macd_histogram_strategy import MacdHistogramStrategy
from ..strategy.rsi_trend_don_chain_strategy import RsiTrendDonChainStrategy
from ..strategy.ut_bot_strategy import UTBotStrategy

log = logging.getLogger(__name__)


async def smart_bot(currency="ETH"):
    query_symbol = f"{currency}/USD"
    spot_symbol = f"{currency}/USD"
    future_symbol = f"{currency}/USDT"
    strategy = UTBotStrategy(symbol=spot_symbol)
    # somehow gemini only return finished timeframe data
    data = fetch_data(query_symbol, "H1", False, limit=1500)
    log.info(f"fetching data for {spot_symbol} {data.index[-1]}")
    d_data = resample_to_interval(data, 360)
    # d_data = fetch_data(query_symbol, "H4", True, counts=1500)

    # opened_position = opened_position_by_symbol(trade_symbol)

    is_exit_trade = strategy.exit_signal(data, d_data)
    trade = get_last_time_trade(spot_symbol)
    if is_exit_trade and trade is not None and trade.status == TradeStatus.closed.name:
        try:
            # disable spot trade for now
            sell_spot(spot_symbol)
            # close_position(future_symbol)
            log.info("closed position!")
            say_something("closed position {}".format(spot_symbol))
        except Exception as err:
            log.error("closed position error! {}".format(err))
            # disable spot trade for now
            sell_spot(spot_symbol)
            # close_position(future_symbol)

    strategy.seek_trend(data, d_data)
    is_opened_trade = strategy.entry_signal(data, d_data)
    trade = get_last_time_trade(spot_symbol)
    if is_opened_trade and trade is not None and trade.status == TradeStatus.opened.name:
        trade_type = TradeType.long if trade.trend == TradeType.long.name else TradeType.short
        try:
            # disable spot trade for now
            if trade_type == TradeType.long:
                buy_spot(spot_symbol)
            # place_trade(future_symbol, "buy", trade_type)
            log.info("opened position!")
            say_something("opened position {}".format(spot_symbol))
        except Exception as err:
            log.error("open position error! {}".format(err))
            # disable spot trade for now
            if trade_type == TradeType.long:
                buy_spot(spot_symbol)
            # place_trade(future_symbol, "buy", trade_type)
            say_something("opened position failed!")
    log.info("job running done!")


async def scan_crypto():
    await smart_bot()


async def trade_forex(symbol="EUR_USD", trading_strategy: type[ABCStrategy] = CCIEMAStrategy, quantity=15000, trade_short_order=True, trade_long_order=True, timeframe="H1"):
    query_symbol = symbol
    trade_symbol = symbol
    strategy = trading_strategy(symbol=query_symbol, trade_short_order=trade_short_order, trade_long_order=trade_long_order)
    data = fetch_data(query_symbol, timeframe, True, counts=2001)
    log.info(f"fetching data for {symbol} {data.index[-1]}")
    # d_data = fetch_data(query_symbol, "H4", True, counts=500)
    d_data = resample_to_interval(data, 10)

    is_exit_trade = strategy.exit_signal(data, day_candles=d_data)
    trade = get_last_time_trade(query_symbol)
    if trade is not None and not has_opened_trades(query_symbol):
        strategy.close_order_by_exchange(data)

    if is_exit_trade and trade is not None and trade.status == TradeStatus.closed.name:
        try:
            close_trade(trade_symbol)
            log.info("closed position!")
            # say_something("closed position {}".format(query_symbol))
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
        atr_data = atr(data.high, data.low, data.close)[-1]
        if trade.trend == TradeType.long.name:
            sl = data.close[-1] - atr_data * 2
            tp = data.close[-1] + atr_data * 3
        else:
            sl = data.close[-1] + atr_data * 2
            tp = data.close[-1] - atr_data * 3
        try:
            make_trade(trade_symbol, trade.trend, quantity=quantity, stop_loss=sl, take_profit=tp)
            log.info("opened position!")
            # say_something("opened position {}".format(query_symbol))
        except Exception as err:
            log.error("open position error! {}".format(err))
            make_trade(trade_symbol, trade.trend, quantity=quantity, stop_loss=sl, take_profit=tp)
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
        # await trade_forex(symbol="USD_JPY", trading_strategy=EmaSqueezeStrategy, quantity=5000)
        # await trade_forex(symbol="AUD_USD", trading_strategy=LogisticRegressionStrategy, quantity=5000)
        # await trade_forex(symbol="EUR_USD", trading_strategy=LogisticRegressionStrategy, quantity=5000, trade_short_order=False)
        log.info("stop h1 job scanner")
    except Exception as err:
        log.error(str(err))

    # await trade_forex(trading_strategy=LogisticRegressionStrategy)
    # await trade_forex(symbol="WTICO_USD", trading_strategy=UTBotStrategy, quantity=80)

async def smart_dog(currency="DOGE"):
    query_symbol = f"{currency}/USDT"
    spot_symbol = f"{currency}/USD"
    future_symbol = f"{currency}/USDT"
    strategy = BBAdxRsiV2(symbol=spot_symbol)
    # somehow gemini only return finished timeframe data
    data = binance_fetcher(query_symbol, "M5", True, limit=2001)
    log.info(f"fetching data for {spot_symbol} {data.index[-1]}")
    d_data = resample_to_interval(data, 360)
    # d_data = fetch_data(query_symbol, "H4", True, counts=1500)

    # opened_position = opened_position_by_symbol(trade_symbol)

    is_exit_trade = strategy.exit_signal(data, d_data)
    trade = get_last_time_trade(spot_symbol)
    if is_exit_trade and trade is not None and trade.status == TradeStatus.closed.name:
        try:
            # disable spot trade for now
            close_position(future_symbol)
            log.info("closed position!")
        except Exception as err:
            log.error("closed position error! {}".format(err))
            # disable spot trade for now
            close_position(future_symbol)

    strategy.seek_trend(data, d_data)
    is_opened_trade = strategy.entry_signal(data, d_data)
    trade = get_last_time_trade(spot_symbol)
    if is_opened_trade and trade is not None and trade.status == TradeStatus.opened.name:
        trade_type = TradeType.long if trade.trend == TradeType.long.name else TradeType.short
        atr_data = atr(data.high, data.low, data.close)[-1]
        if trade.trend == TradeType.long.name:
            sl = data.close[-1] - atr_data * 2
            tp = data.close[-1] + atr_data * 3
        else:
            sl = data.close[-1] + atr_data * 2
            tp = data.close[-1] - atr_data * 3
        try:
            place_trade(future_symbol, "buy", trade_type, sl=sl, tp=tp)
            log.info("opened position!")
        except Exception as err:
            log.error("open position error! {}".format(err))
            place_trade(future_symbol, "buy", trade_type, sl=atr_data*2, tp=atr_data*3)
    log.info("job running done!")


async def scanner_job():
    await asyncio.sleep(10)
    for instrument in Instruments:
        await trade_forex(symbol=instrument, timeframe="M5", trading_strategy=MacdHistogramStrategy, quantity=5000)
    await smart_dog()
    # await smart_dog("ADA")
    # await smart_dog("ATOM")
    # await smart_dog("XRP")
    # await smart_dog("SOL")
    await smart_dog("DOT")


async def scanner_h1_job():
    await scanner_job()
    await scan_forex()
    await asyncio.sleep(60)
    await scan_crypto()
