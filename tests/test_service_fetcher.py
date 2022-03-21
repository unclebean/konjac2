from konjac2.service.fetcher import fetch_data


def test_fetch_forex_data(mocker):
    mocker.patch("konjac2.service.fetcher.forex_fetcher", return_value=2)
    assert fetch_data("EUR_USD", "D", True) == 2


def test_fetch_crypto_data(mocker):
    mocker.patch("konjac2.service.fetcher.crypto_fetcher", return_value=3)
    assert fetch_data("ETH/USDT", "D", True) == 3
