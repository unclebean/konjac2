import numpy as np
import pandas as pd
from pandas_ta import amat, aroon, chop, decay, decreasing, dpo, increasing, psar, qstick, ttm_trend, vhf, \
    vortex, ao, apo, bias, bop, brar, cfo, cg, cmo, coppock, er, fisher, inertia, kdj, kst, sma
from pandas_ta.overlap import ema, ichimoku
from pandas_ta.volatility import bbands, atr
from pandas_ta.momentum import macd, cci, rsi, stoch, mom
from pandas_ta.volume import obv
from pandas_ta.trend import adx
from sklearn.linear_model import LogisticRegression
import xgboost as xgb
from sklearn.preprocessing import MinMaxScaler
from .vwap import VWAP
from ..chart.heikin_ashi import heikin_ashi

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
    y = np.where(candles["close"].shift(-1) > candles["high"], 1, -1)[2:]
    X_train, X_test, y_train, y_test = X[:split], X[split:], y[:split], y[split:]
    model = LogisticRegression()
    model = model.fit(X_train, y_train)
    return model.predict(candles.iloc[-1:, :16]), model.score(X_test, y_test)


def predict_xgb_next_ticker(candelstick, predict_step=1, model=None, delta_hours=0, for_trend=True):
    data_y, data_x = prepare_indicators_data(candelstick, delta_hours, for_trend=for_trend)
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
    # model = xgb.train(_get_params(), data_dmatrix)
    features = feature_importance(model)
    predict_score = model.predict(xgb.DMatrix(test_x))
    return predict_score, accuracy, features


def feature_importance(model):
    feat_importances = []
    for ft, score in model.get_fscore().items():
        feat_importances.append({"Feature": ft, "Importance": score})
    return feat_importances


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


def prepare_indicators_data(candlestick, delta_hours=0, for_trend=True):
    result = np.where(candlestick["close"].shift(-1) > candlestick["close"], 1, 0)[1:]
    # candlestick.apply(lambda row: 1 if row.close > row.open else 0, axis=1)
    indicators = trend_params(candlestick) if for_trend else rsi_stoch_macd_params(candlestick)

    (count_y,) = result.shape
    merged_indicators = indicators
    # merged_indicators = merge_lag_data(indicators)

    merged_indicators = pd.DataFrame(scaler.fit_transform(merged_indicators), columns=merged_indicators.columns)

    row_x, _ = merged_indicators.shape

    return result, merged_indicators[1:]


def sol_params(candlestick):
    heikin_ashi_data = heikin_ashi(candlestick)

    close_price = heikin_ashi_data.close
    obv_values = obv(close_price, heikin_ashi_data.volume)
    obv_ema200 = ema(obv_values, 200)

    return pd.DataFrame(
        {
            "close_shift1": close_price - close_price.shift(1),
            "close_shift2": close_price.shift(1) - close_price.shift(2),
            "close_shift3": close_price.shift(2) - close_price.shift(3),
            "close_shift4": close_price.shift(3) - close_price.shift(4),
            "close_shift5": close_price.shift(4) - close_price.shift(5),
        },
        index=candlestick.index,
    )


def momentum_params(candles):
    ao_ = ao(candles.high, candles.low)
    apo_ = apo(candles.close)
    bias_ = bias(candles.close)
    bop_ = bop(candles.open, candles.high, candles.low, candles.close)
    brar_ = brar(candles.open, candles.high, candles.low, candles.close)
    cci_ = cci(candles.high, candles.low, candles.close)
    cfo_ = cfo(candles.close)
    cg_ = cg(candles.close)
    cmo_ = cmo(candles.close)
    coppock_ = coppock(candles.close)
    er_ = er(candles.close)
    fisher_ = fisher(candles.high, candles.low)
    inertia_ = inertia(candles.close, candles.high, candles.low)
    kdj_ = kdj(candles.high, candles.low, candles.close)
    kst_ = kst(candles.close)
    indicators = pd.concat([ao_, apo_, bias_, bop_, brar_, cci_, cfo_, cg_, cmo_, coppock_, er_, fisher_, inertia_, kdj_, kst_], axis=1)

    return indicators

def trend_params(candles):
    adx_ = adx(candles.high, candles.low, candles.close)
    amat_ = amat(candles.close)
    aroon_ = aroon(candles.high, candles.low)
    chop_ = chop(candles.high, candles.low, candles.close)
    decay_ = decay(candles.close)
    decreasing_ = decreasing(candles.close)
    dpo_ = dpo(candles.close)
    increasing_ = increasing(candles.close)
    psar_ = psar(candles.high, candles.low, candles.close)
    qstick_ = qstick(candles.open, candles.close)
    ttm_ = ttm_trend(candles.high, candles.low, candles.close)
    vhf_ = vhf(candles.close)
    vortex_ = vortex(candles.high, candles.low, candles.close)
    indicators = adx_.join(amat_) \
        .join(aroon_) \
        .join(chop_) \
        .join(decay_) \
        .join(decreasing_) \
        .join(dpo_) \
        .join(increasing_) \
        .join(psar_) \
        .join(qstick_) \
        .join(ttm_) \
        .join(vhf_) \
        .join(vortex_)
    return indicators


def new_params(candles):
    # ema3
    ema3 = ema(candles.close, 3)
    # ema10
    ema10 = ema(candles.close, 10)
    # ema100
    ema100 = ema(candles.close, 100)
    # macd
    macd_df = macd(candles.close)
    macd_values = macd_df["MACD_12_26_9"]
    # macd signal diff
    macd_signals = macd_df["MACDs_12_26_9"]
    # adx 20
    adx_df = adx(candles.high, candles.low, candles.close, 20)
    adx20 = adx_df["ADX_20"]
    # pdi mdi diff
    # sto slowk
    sto_df = stoch(candles.high, candles.low, candles.close)

    sto_k = sto_df["STOCHk_14_3_3"]
    # sto diff
    sto_d = sto_df["STOCHd_14_3_3"]
    # cci3
    cci3 = cci(candles.high, candles.low, candles.close, 3)
    # cci10
    cci10 = cci(candles.high, candles.low, candles.close, 10)
    # mom3
    mom3 = mom(candles.close, 3)
    # mom10
    mom10 = mom(candles.close, 10)
    # atr3
    atr3 = atr(candles.high, candles.low, candles.close, 3)
    # atr10
    atr10 = atr(candles.high, candles.low, candles.close, 10)
    # bbands3
    bb3 = bbands(candles.close, 3)
    bb3_diff = bb3["BBU_3_2.0"] - bb3["BBL_3_2.0"]
    # bbands10
    bb10 = bbands(candles.close, 10)
    bb10_diff = bb10["BBU_10_2.0"] - bb10["BBL_10_2.0"]
    return pd.DataFrame(
        {
            "ema3": ema3,
            "ema10": ema10,
            "ema100": ema100,
            "macd_values": macd_values,
            "macd_signals": macd_signals,
            "adx20": adx20,
            "sto_k": sto_k,
            "sto_d": sto_d,
            "cci3": cci3,
            "cci10": cci10,
            "mom3": mom3,
            "mom10": mom10,
            "atr3": atr3,
            "atr10": atr10,
            "bb3_diff": bb3_diff,
            "bb10_diff": bb10_diff,
        },
        index=candles.index,
    )


def rsi_stoch_macd_params(candles):
    stoch_data = stoch(candles.high, candles.low, candles.close)
    stoch_k = stoch_data["STOCHk_14_3_3"]
    stoch_d = stoch_data["STOCHd_14_3_3"]
    rsi_data = rsi(candles.close, length=14)
    rsi_sma_data = sma(rsi_data, length=14)
    macd_data = macd(candles.close)
    macd_ = macd_data["MACD_12_26_9"]
    macd_signal = macd_data["MACDs_12_26_9"]
    return pd.DataFrame(
        {
            "stoch": stoch_k - stoch_d,
            "rsi_sma": rsi_data - rsi_sma_data,
            "macd": macd_ - macd_signal
        },
        index=candles.index,
    )


def merge_lag_data(df):
    index = df.index
    df = df.append(pd.Series(dtype="float64"), ignore_index=True)
    merge_key = "order_day"
    df["order_day"] = [x for x in list(range(len(df)))]
    lag_cols = [
        "open_vwap",
        "high_vwap",
        "low_vwap",
        "close_vwap",
        "obv_ema",
        "rsi_ema",
        "cci_ema",
        "close_ema",
        "close_shift1",
    ]

    def rename_col(x):
        return "{}_lag_{}".format(x, shift) if x in lag_cols else x

    for shift in [x + 1 for x in range(5)]:
        shift_data = df[[merge_key] + lag_cols].copy()
        shift_data[merge_key] = shift_data[merge_key] + shift
        shift_data = shift_data.rename(columns=rename_col)
        df = pd.merge(df, shift_data, on=[merge_key], how="left")
    df = df.drop(columns=lag_cols + [merge_key])[1:]
    df.index = index
    return df[5:]


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
