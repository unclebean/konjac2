import ccxt
from konjac2.config import settings


def get_context(account=""):
    if account == "spot":
        return ccxt.ftx(
            {
                "headers": {
                    "FTX-SUBACCOUNT": "SPOT",
                },
                "apiKey": settings.ftx_spot_api_key,
                "secret": settings.ftx_spot_secret,
                "options": {
                    "defaultType": "future",  # or 'margin'
                },
            }
        )
    exchange = ccxt.ftx(
        {
            "apiKey": settings.ftx_future_api_key,
            "secret": settings.ftx_future_secret,
            "options": {
                "defaultType": "future",  # or 'margin'
            },
        },
    )
    return exchange


def get_binance_context():

    exchange = ccxt.binance(
        {
            "apiKey": settings.binance_api_key,
            "secret": settings.binance_secret,
            "options": {"defaultMarket": "futures"},
        },
    )
    return exchange
