import re
from datetime import datetime

FX_STOP_LOSS = 0.0025
FX_JPY_STOP_LOSS = 0.25
FX_TAKE_PROFIT = 0.005
FX_JPY_TAKE_PROFIT = 0.5

CP_STOP_LOSS = 0.08
CP_TAKE_PROFIT = 0.08


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


def get_stop_loss(symbol: str):
    if is_forex_symbol(symbol):
        if "JPY" in symbol:
            return FX_JPY_STOP_LOSS
        return FX_STOP_LOSS

    if is_crypto_symbol(symbol):
        return CP_STOP_LOSS


def get_take_profit(symbol: str):
    if is_forex_symbol(symbol):
        if "JPY" in symbol:
            return FX_JPY_TAKE_PROFIT
        return FX_TAKE_PROFIT

    if is_crypto_symbol(symbol):
        return CP_TAKE_PROFIT

