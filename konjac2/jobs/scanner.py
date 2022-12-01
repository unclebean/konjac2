import asyncio
import logging
from datetime import datetime as dt

from pandas_ta import willr

from konjac2.bot.telegram_bot import say_something
from konjac2.models.trade import TradeStatus, get_last_time_trade
from konjac2.service.crypto.fetcher import place_trade
from konjac2.service.fetcher import fetch_data
from konjac2.indicator.heikin_ashi_momentum import heikin_ashi_mom
from konjac2.indicator.squeeze_momentum import squeeze
from konjac2.indicator.hurst import hurst
from konjac2.models import apply_session
from konjac2.models.trend import TradingTrend
from konjac2.indicator.utils import TradeType, resample_to_interval
from konjac2.service.forex.place_order import close_trade, has_opened_trades, make_trade, is_opened_maximum_positions
from konjac2.strategy.bbcci_strategy import BBCCIStrategy
from konjac2.strategy.logistic_regression_strategy import LogisticRegressionStrategy
from . import Instruments, Cryptos
from ..indicator.moving_average import moving_average
from ..service.crypto.gemini import sell_spot, buy_spot, opened_position_by_symbol
from ..service.utils import filter_incomplete_h4_data
from ..strategy.abc_strategy import ABCStrategy
from ..strategy.cci_ema_strategy import CCIEMAStrategy
from ..strategy.dema_supertrend_strategy import DemaSuperTrendStrategy
from ..strategy.ema_ma_rsi_strategy import EmaMaRsiStrategy
from ..strategy.ichimoku_will_v2_strategy import IchimokuWillRV2
from ..strategy.ichimoku_willr_strategy import IchimokuWillR
from ..strategy.macd_histogram_strategy import MacdHistogramStrategy
from ..strategy.macd_rsi_vwap_strategy import MacdRsiVwapStrategy
from ..strategy.macd_strategy import MacdStrategy
from ..strategy.ut_bot_strategy import UTBotStrategy
from ..strategy.ut_super_trend_strategy import UTSuperTrendStrategy
from ..strategy.vwap_rsi_strategy import VwapRsiStrategy
from ..strategy.vwap_rsi_willr_strategy import VwapRsiWillR

log = logging.getLogger(__name__)


async def smart_bot(currency="ETH"):
    query_symbol = f"{currency}/USD"
    trade_symbol = f"{currency}/USD"
    strategy = UTBotStrategy(symbol=query_symbol, trade_short_order=False)
    data = fetch_data(query_symbol, "H1", True, limit=1500)
    log.info(f"fetching data for {query_symbol} {data.index[-1]}")
    d_data = resample_to_interval(data, 360)
    # d_data = fetch_data(query_symbol, "H4", True, counts=1500)

    # opened_position = opened_position_by_symbol(trade_symbol)

    is_exit_trade = strategy.exit_signal(data, d_data)
    trade = get_last_time_trade(query_symbol)
    if is_exit_trade and trade is not None and trade.status == TradeStatus.closed.name:
        try:
            sell_spot(trade_symbol)
            log.info("closed position!")
            say_something("closed position {}".format(query_symbol))
        except Exception as err:
            log.error("closed position error! {}".format(err))
            sell_spot(trade_symbol)

    strategy.seek_trend(data, d_data)
    is_opened_trade = strategy.entry_signal(data, d_data)
    trade = get_last_time_trade(query_symbol)
    if is_opened_trade and trade is not None and trade.status == TradeStatus.opened.name:
        try:
            buy_spot(trade_symbol)
            log.info("opened position!")
            say_something("opened position {}".format(query_symbol))
        except Exception as err:
            log.error("open position error! {}".format(err))
            buy_spot(trade_symbol)
            say_something("opened position failed!")
    log.info("job running done!")


async def scan_crypto():
    await smart_bot()


async def close_all_crypto():
    for currency in Cryptos:
        trade_symbol = f"{currency}-PERP"
        opened_position = opened_position_by_symbol(trade_symbol)
        if opened_position:
            place_trade(trade_symbol, "sell")


async def trade_forex(symbol="EUR_USD", trading_strategy: type[ABCStrategy] = CCIEMAStrategy):
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
            make_trade(trade_symbol, trade.trend)
            log.info("opened position!")
            say_something("opened position {}".format(query_symbol))
        except Exception as err:
            log.error("open position error! {}".format(err))
            make_trade(trade_symbol, trade.trend)
            say_something("opened position failed!")
    log.info("job running done!")


async def retrieve_fx_position_state(symbol):
    if has_opened_trades(symbol):
        data = fetch_data(symbol, "H1", False, counts=500)
        willr_ = willr(data.high, data.low, data.close)
        if willr_[-1] > -30 or willr_[-1] < -70:
            say_something("{} should consider close {}".format(symbol, willr_[-1]))


async def scan_forex():
    for instrument in Instruments:
        try:
            if is_opened_maximum_positions():
                break
            await trade_forex(instrument)
        except Exception as err:
            print(str(err))

    await trade_forex(trading_strategy=LogisticRegressionStrategy)


async def place_crypto_order(symbol: str, trend: str):
    if symbol is not None and trend is not None and not has_opened_trades(symbol):
        data = fetch_data(symbol, "H1", True, counts=100)
        ma = moving_average(data.close)
        stop_position = ma[-1] - ma[-1] * 0.002 if trend == TradeType.long.name else ma[-1] + ma[-1] * 0.002
        place_trade(symbol, "buy", trend)


async def scanner_job():
    for instrument in Instruments:
        pass
        # await retrieve_fx_position_state(instrument)


async def scanner_h1_job():
    await asyncio.sleep(30)
    await scan_forex()
    await asyncio.sleep(60)
    await scan_crypto()
