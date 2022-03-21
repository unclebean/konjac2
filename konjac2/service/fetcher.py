import re
from pydantic import validate_arguments
from .forex.fetcher import forex_fetcher
from .equity.fetcher import equity_fetcher
from .crypto.fetcher import crypto_fetcher


@validate_arguments
def fetch_data(symbol: str, timeframe: str, complete: bool, **kwargs):
    fetcher = _get_delegator_by_symbol(symbol=symbol)
    return fetcher(symbol, timeframe, complete, kwargs)


@validate_arguments
def _get_delegator_by_symbol(symbol: str):
    is_forex_symbol = re.search(r".*_.*", symbol)
    is_crypto_symbol = re.search(r".*[-|/].*", symbol)
    if is_forex_symbol is not None:
        return forex_fetcher

    if is_crypto_symbol is not None:
        return crypto_fetcher

    return equity_fetcher
