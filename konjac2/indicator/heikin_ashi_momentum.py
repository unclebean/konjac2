from ..chart.heikin_ashi import heikin_ashi


def heikin_ashi_mom(long_term_volatility_data, short_term_volatility_data):
    short_term_heikin_ashi = heikin_ashi(short_term_volatility_data)
    long_term_volatility = (
        long_term_volatility_data["high"] - long_term_volatility_data["low"]
    ) / long_term_volatility_data["high"]
    average_dv = long_term_volatility.abs().rolling(7).apply(lambda d: d.sum() / 7)
    # volatility/3 for the threadholder
    threadholder = average_dv / 3
    # getting 6H heikin_ashi
    # close - open for volatility of heikin_ashi bar
    short_term_volatility = (
        (short_term_heikin_ashi["close"] - short_term_heikin_ashi["open"])
    ) / short_term_heikin_ashi["close"]

    return threadholder, short_term_volatility
