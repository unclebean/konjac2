import yfinance as yf


def equity_fetcher(symbol, period="3m0", interval="60"):
    return yf.download(symbol, period=period, interval=interval)
