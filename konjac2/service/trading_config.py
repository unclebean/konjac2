from functools import cache

import tomli


@cache
def trading_config():
    with open("trading-config.toml", "rb") as f:
        toml_dict = tomli.load(f)
        return toml_dict


def get_fx_config():
    fx_config = trading_config()
    return fx_config["forex"]


def get_fx_symbol_list():
    fx_config = get_fx_config()
    return fx_config["symbol_list"]


def get_fx_trade_quantity():
    fx_config = get_fx_config()
    return fx_config["quantity"]


def get_fx_stop_loss(symbol: str):
    fx_config = get_fx_config()
    if "JPY" in symbol:
        return fx_config["jpy_stop_lose"]
    return fx_config["stop_lose"]
