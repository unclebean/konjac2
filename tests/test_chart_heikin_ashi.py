import pandas as pd
from konjac2.chart.heikin_ashi import heikin_ashi


data = {
    "open": [1.19808, 1.2049],
    "high": [1.19845, 1.20502],
    "low": [1.19574, 1.20461],
    "close": [1.1966, 1.20466],
    "volume": [19678, 1477],
}
candlestick_df = pd.DataFrame(
    data=data,
    index=[
        "2021-02-04 15:00:00",
        "2021-02-04 21:00:00",
    ],
)


def test_heikin_ashi_chart():
    chart_data = heikin_ashi(candlestick_df)
    assert chart_data.volume[-1] == 1477
    assert round(chart_data.close[-1], 7) == 1.2047975
    assert chart_data.open[-1] == 1.19764875
