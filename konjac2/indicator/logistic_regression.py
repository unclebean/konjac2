import numpy as np
import pandas as pd
from pandas_ta.overlap import ema, ichimoku
from pandas_ta.volatility import bbands
from pandas_ta.momentum import macd, cci, rsi
from sklearn.linear_model import LogisticRegression
import xgboost as xgb
from sklearn.preprocessing import MinMaxScaler
from .vwap import VWAP

scaler = MinMaxScaler()
period = 34
period21 = 21
period13 = 13


def LogisticRegressionModel(candles):
    split = int(0.8 * len(candles))
    candles["S_10"] = candles["close"].rolling(window=21).mean()
    candles["Corr"] = candles["close"].rolling(window=21).corr(candles["S_10"])
    # candles["Open-Close"] = candles["open"] - candles["close"].shift(1)
    # candles["Open-Open"] = candles["open"] - candles["open"].shift(1)
    ichimoku_df, _ = ichimoku(candles.high, candles.low, candles.close)
    candles["t-k"] = ichimoku_df["ITS_9"] - ichimoku_df["IKS_26"]
    candles["s-s"] = ichimoku_df["ISA_9"] - ichimoku_df["ISB_26"]
    candles["macd"] = macd_to_series(candles.close)
    candles["bbands"] = bbands_to_series(candles.close, 21)
    candles["cci"] = cci_to_series(candles.high, candles.low, candles.close, 21)
    candles["rsi"] = rsi_to_series(candles.close, 21)
    candles["vwap"] = vwap_to_series(candles, 0)
    candles["efi"] = efi_to_series(candles.close, candles.volume, 13)
    candles["ema"] = ema_to_serires(candles.close)

    candles = candles.dropna()
    X = candles.iloc[0:-2, :16]
    y = np.where(candles["close"].shift(-1) > candles["close"], 1, -1)[2:]
    X_train, X_test, y_train, y_test = X[:split], X[split:], y[:split], y[split:]
    model = LogisticRegression()
    model = model.fit(X_train, y_train)
    return model.predict(candles.iloc[-1:, :16]), model.score(X_test, y_test)


def predict_xgb_next_ticker(candelstick, predict_step=1, model=None, delta_hours=0):
    data_y, data_x = prepare_indicators_data(candelstick, delta_hours)
    if predict_step == 0:
        train_x = data_x[1:]
        train_y = data_y[1:]
        test_x = data_x[-1:]
    else:
        train_x = data_x.shift(predict_step)[predict_step:]
        train_y = data_y[predict_step:]
        test_x = data_x[-predict_step:]

    data_dmatrix = xgb.DMatrix(data=train_x, label=train_y)
    accuracy = _cross_validate(data_dmatrix)
    model = xgb.train(_get_params(), data_dmatrix)

    predict_score = model.predict(xgb.DMatrix(test_x))
    return predict_score, accuracy


def feature_importance(model):
    feat_importances = []
    for ft, score in model.get_fscore().items():
        feat_importances.append({"Feature": ft, "Importance": score})
    print(feat_importances)


def _cross_validate(trainData):
    cv_results = xgb.cv(
        dtrain=trainData,
        params=_get_params(),
        nfold=4,
        num_boost_round=10,
        metrics="error",
        as_pandas=True,
    )
    return (1 - cv_results["test-error-mean"]).iloc[-1]


def _get_params():
    params_dict = dict()
    params_dict["learning_rate"] = 0.05
    params_dict["objective"] = "reg:logistic"
    params_dict["max_depth"] = 3
    params_dict["min_child_weight"] = 50
    params_dict["gamma"] = 0
    params_dict["subsample"] = 0.8
    params_dict["colsample_bytree"] = 1.0
    params_dict["tree_method"] = "hist"
    params_dict["reg_alpha"] = 0.0
    params_dict["reg_lambda"] = 1.0
    params_dict["eval_metric"] = "auc"
    params_dict["nthread"] = 2
    params_dict["scale_pos_weight"] = 1
    params_dict["seed"] = 0
    return params_dict


def prepare_indicators_data(candlestick, delta_hours=0):
    result = candlestick.apply(lambda row: 1 if row.close > row.open else 0, axis=1)
    open = candlestick.open
    close = candlestick.close
    high = candlestick.high
    low = candlestick.low
    close = candlestick.close
    volume = candlestick.volume
    macd_values = macd_to_series(close)
    cci_values = cci_to_series(high, low, close, period)
    bbands_values = bbands_to_series(close, period)
    rsi_values = rsi_to_series(close, period)
    efi_values = efi_to_series(close, volume, period)

    cci_values21 = cci_to_series(high, low, close, period21)
    bbands_values21 = bbands_to_series(close, period21)
    rsi_values21 = rsi_to_series(close, period21)
    efi_values21 = efi_to_series(close, volume, period21)

    cci_values13 = cci_to_series(high, low, close, period13)
    bbands_values13 = bbands_to_series(close, period13)
    rsi_values13 = rsi_to_series(close, period13)
    efi_values13 = efi_to_series(close, volume, period13)

    vwap_values = vwap_to_series(candlestick, delta_hours)
    ema_values = ema_to_serires(close)

    ichimoku_df, _ = ichimoku(candlestick.high, candlestick.low, candlestick.close)

    indicators = pd.DataFrame(
        {
            "macd": macd_values,
            "cci": cci_values,
            "bbands": bbands_values,
            "rsi": rsi_values,
            "t-k": ichimoku_df["ITS_9"] - ichimoku_df["IKS_26"],
            "s-s": ichimoku_df["ISA_9"] - ichimoku_df["ISB_26"],
            "vwap": vwap_values,
            "efi": efi_values,
            "cci21": cci_values21,
            "rsi21": rsi_values21,
            "bbands21": bbands_values21,
            "efi21": efi_values21,
            "cci13": cci_values13,
            "rsi13": rsi_values13,
            "bbands13": bbands_values13,
            "efi13": efi_values13,
            "ema": ema_values,
        },
        index=candlestick.index,
    )

    (count_y,) = result.shape
    # merged_indicators = indicators
    merged_indicators = merge_lag_data(indicators)

    merged_indicators = pd.DataFrame(scaler.fit_transform(merged_indicators), columns=merged_indicators.columns)

    row_x, _ = merged_indicators.shape

    return result[(count_y - row_x) :], merged_indicators


def merge_lag_data(df):
    index = df.index
    df = df.append(pd.Series(), ignore_index=True)
    merge_key = "order_day"
    df["order_day"] = [x for x in list(range(len(df)))]
    lag_cols = [
        "macd",
        "cci",
        "bbands",
        "rsi",
        "vwap",
        "efi",
        "cci21",
        "rsi21",
        "bbands21",
        "efi21",
        "cci13",
        "rsi13",
        "bbands13",
        "efi13",
        "ema",
    ]

    def rename_col(x):
        return "{}_lag_{}".format(x, shift) if x in lag_cols else x

    for shift in [x + 1 for x in range(3)]:
        shift_data = df[[merge_key] + lag_cols].copy()
        shift_data[merge_key] = shift_data[merge_key] + shift
        shift_data = shift_data.rename(columns=rename_col)
        df = pd.merge(df, shift_data, on=[merge_key], how="left")
    df = df.drop(columns=lag_cols + [merge_key])[1:]
    df.index = index
    return df[3:]


def macd_to_series(close):
    macd_df = macd(close)
    values = []
    for (m, s, h) in zip(macd_df["MACD_12_26_9"], macd_df["MACDs_12_26_9"], macd_df["MACDh_12_26_9"]):
        values.append(m - s)
    return values


def bbands_to_series(close, period):
    bb_df = bbands(close, timeperiod=period)
    values = []
    for i, (u, m, l) in enumerate(zip(bb_df["BBU_5_2.0"], bb_df["BBM_5_2.0"], bb_df["BBL_5_2.0"])):
        if close[i] > m:
            values.append((u - close[i]))
        elif close[i] < m:
            values.append((l - close[i]))
        else:
            values.append(0)
    return pd.Series(values, bb_df["BBU_5_2.0"].index)


def cci_to_series(high, low, close, period):
    cci_series = cci(high, low, close, timeperiod=period)
    return cci_series.values


def rsi_to_series(close, period):
    rsi_series = rsi(close, timeperiod=period)
    return rsi_series.values


def vwap_to_series(candlesticks, delta_hours):
    close = candlesticks.close
    vwap, upper_band, lower_band = VWAP(candlestick=candlesticks, delta_hours=delta_hours, group_by="day")
    values = []
    for i, (u, v, l) in enumerate(zip(upper_band, vwap, lower_band)):
        if close[i] > v:
            values.append((u - close[i]))
        elif close[i] < v:
            values.append((l - close[i]))
        else:
            values.append(0)

    return pd.Series(values, upper_band.index)


def efi_to_series(close, volume, period):
    close_times_volume = close.diff(1) * volume
    efi = close_times_volume.ewm(ignore_na=False, span=period).mean()
    return efi


def ema_to_serires(close):
    fast = ema(close, 20).values
    slow = ema(close, 50).values
    return fast - slow
