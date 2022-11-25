from konjac2.service.fetcher import fetch_data


def test_fetch_forex_data(mocker):
    mocker.patch("konjac2.service.fetcher.forex_fetcher", return_value=2)
    assert fetch_data("EUR_USD", "D", True) == 2


def test_fetch_crypto_data(mocker):
    mocker.patch("konjac2.service.fetcher.crypto_fetcher", return_value=3)
    assert fetch_data("ETH/USDT", "D", True) == 3


# Write a function to dispense change to a customer, using the minimum number of coins possible to add up to the total.

# You may dispense any number of 1p, 5p, 10p, 20p coins to make up the total.

# Your function should accept an integer, and should print the number of coins of each type used.

# For example:

# to dispense 17p with the least coins would take 1x 10p coin, 1x 5p coin and 2x 1p coins.
# to dispense 128p with the least coins would take 6x 20p coins, 1x 5p coin and 3x 1p coins.

# [ ]

coins = [20, 13, 10, 5, 1]


def dispense(total: int, coins):
    if len(coins) == 0:
        return
    current_coin = coins.pop(0)
    if total > current_coin:
        dispense_coins = int(total / current_coin)
        remain = total % current_coin
        print(f"{dispense_coins}* {current_coin}p")
        dispense(remain, coins)
    else:
        dispense(total, coins)


dispense(26, coins)