from konjac2.service.fetcher import fetch_data
from konjac2.indicator.heikin_ashi_momentum import heikin_ashi_mom
from konjac2.indicator.squeeze_momentum import squeeze
from konjac2.indicator.hurst import hurst


def forex_scanner():
    day_data = fetch_data("GBP_JPY", "D", False)
    h6_data = fetch_data("GBP_JPY", "H6", False)
    m30_data = fetch_data("GBP_JPY", "M30", False, counts=1597)

    trends, is_sqz_off, mom = squeeze(m30_data)
    is_sqz = not is_sqz_off[-1]
    hurst_result = hurst(m30_data.close.values)
    print(f"hurst {hurst_result}")

    order_action = None
    if trends[-1] > 0 and mom[-1] > 0 and hurst_result > 0.5 and is_sqz is not True:
        order_action = "long"
    if trends[-1] < 0 and mom[-1] < 0 and hurst_result > 0.5 and is_sqz is not True:
        order_action = "short"

    threadholder, short_term_volatility = heikin_ashi_mom(day_data, h6_data)

    trend_action = None
    if threadholder[-1] <= abs(short_term_volatility[-1]) and short_term_volatility[-1] > 0:
        trend_action = "long"

    if threadholder[-1] <= abs(short_term_volatility[-1]) and short_term_volatility[-1] < 0:
        trend_action = "short"

    print(f"trend {trend_action} order {order_action}")
