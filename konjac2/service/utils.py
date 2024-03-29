import re
import math
from datetime import datetime


FX_STOP_LOSS = 0.0035
FX_JPY_STOP_LOSS = 0.35
FX_TAKE_PROFIT = 0.0035
FX_JPY_TAKE_PROFIT = 0.35
FX_WTICO_TAKE_PROFIT = 0.7
FX_WTICO_STOP_LOSS = 0.4

CP_STOP_LOSS = 0.03
CP_TAKE_PROFIT = 0.03
ETH_STOP_LOSS = 0.05
ETH_TAKE_PROFIT = 0.08

CP_MARGIN = 7.5
CP_TRADING_INSTRUMENTS = 1


def get_nearest_complete_h4_hour():
    current_hour = datetime.utcnow().hour - 1
    if 4 <= current_hour < 8:
        return 0
    elif 8 <= current_hour < 12:
        return 4
    elif 12 <= current_hour < 16:
        return 8
    elif 16 <= current_hour < 20:
        return 12
    elif 20 <= current_hour <= 23:
        return 16
    else:
        return 20


def filter_incomplete_h1_data(h1_data):
    current_hour = datetime.utcnow().hour
    last_index_hour = h1_data.index[-1].hour
    if last_index_hour < current_hour:
        return h1_data
    return h1_data[:-1]


def filter_incomplete_h4_data(h4_data):
    return h4_data


def is_forex_symbol(symbol: str) -> bool:
    forex_symbol = re.search(r".*_.*", symbol)
    return forex_symbol is not None


def is_crypto_symbol(symbol: str) -> bool:
    crypto_symbol = re.search(r".*[-|/].*", symbol)
    return crypto_symbol is not None


def get_fx_stop_loss_rate(symbol: str):
    loss = FX_STOP_LOSS
    if "JPY" in symbol:
        loss = FX_JPY_STOP_LOSS
    if "WTICO" in symbol:
        loss = FX_WTICO_STOP_LOSS
    return loss


def get_fx_take_profit_rate(symbol: str):
    profit = FX_TAKE_PROFIT
    if "JPY" in symbol:
        profit = FX_JPY_TAKE_PROFIT
    if "WTICO" in symbol:
        profit = FX_WTICO_TAKE_PROFIT
    return profit


def _fx_stop_loss(symbol: str, quantity: float) -> float:
    return quantity * get_fx_stop_loss_rate(symbol)


def _crypto_stop_loss(order_position: float, quantity: float) -> float:
    return order_position * quantity * CP_STOP_LOSS

def _crypto_eth_stop_loss(order_position: float, quantity: float) -> float:
    return order_position * quantity * ETH_STOP_LOSS


def get_stop_loss(symbol: str, order_position: float, quantity: float) -> float:
    if is_forex_symbol(symbol):
        return _fx_stop_loss(symbol, quantity)

    if is_crypto_symbol(symbol):
        if "ETH" in symbol or "MATIC" in symbol:
            return _crypto_eth_stop_loss(order_position, quantity)
        return _crypto_stop_loss(order_position, quantity)


def _fx_take_profit(symbol: str, quantity: float) -> float:
    return get_fx_take_profit_rate(symbol) * quantity


def _crypto_take_profit(order_position: float, quantity: float) -> float:
    return order_position * quantity * CP_TAKE_PROFIT


def _crypto_eth_take_profit(order_position: float, quantity: float) -> float:
    return order_position * quantity * ETH_TAKE_PROFIT


def get_take_profit(symbol: str, order_position: float, quantity: float) -> float:
    if is_forex_symbol(symbol):
        return _fx_take_profit(symbol, quantity)

    if is_crypto_symbol(symbol):
        if "ETH" in symbol or "MATIC" in symbol:
            return _crypto_eth_take_profit(order_position, quantity)
        return _crypto_take_profit(order_position, quantity)


def align_decimal_length(first_number, second_number):
    first_number_decimal_len = len(str(first_number).split('.')[1])
    second_number_decimal_len = len(str(second_number).split('.')[1])

    shortest_decimal_len = first_number_decimal_len \
        if first_number_decimal_len < second_number_decimal_len \
        else second_number_decimal_len
    shortest_len = int("1" + "0" * shortest_decimal_len)
    truncated_first_num = math.trunc(first_number * shortest_len) / shortest_len
    truncated_second_num = math.trunc(second_number * shortest_len) / shortest_len
    return truncated_first_num, truncated_second_num
