import yfinance as yf


def equity_fetcher(symbol, period="2y", interval="60m"):
    return yf.download(symbol, period=period, interval=interval)
