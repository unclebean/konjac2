# Import the necessary libraries
import xgboost as xgb
from pandas_ta import ema, rsi, adx, amat, aroon, chop, decay, decreasing, dpo, increasing, psar, qstick, ttm_trend, \
    vhf, vortex

from konjac2.indicator.utils import TradeType


def regressor_predict(candles):
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
    candles = candles.join(adx_) \
        .join(amat_) \
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
    train = candles[:int(0.8 * len(candles))]
    test = candles[int(0.8 * len(candles)):]

    # Define the features and target variable
    X_train = train.drop(['close'], axis=1)
    y_train = train['close']
    X_test = test.drop(['close'], axis=1)
    y_test = test['close']



    # Train the XGBoost model
    model = xgb.XGBRegressor()
    model.fit(X_train, y_train)

    # Make predictions on the test set
    predictions = model.predict(X_test)
    print(predictions[-1])

    # Implement your trading strategy based on the predicted values
    if predictions[-1] > y_test.iloc[-1]:
        # Buy signal
        return TradeType.long.name
    else:
        # Sell signal
        return TradeType.short.name


def logistic_predict(candles):
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
    candles = candles.join(adx_) \
        .join(amat_) \
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
    candles['target'] = candles['close'].shift(-1) > candles['close']

    # Split the data into training and test sets
    train = candles[:int(0.8 * len(candles))]
    test = candles[int(0.8 * len(candles)):]

    # Define the features and target variable
    X_train = train.drop(['target'], axis=1)
    y_train = train['target']
    X_test = test.drop(['target'], axis=1)
    y_test = test['target']

    # Train the XGBoost model
    model = xgb.XGBClassifier()
    model.fit(X_train, y_train)

    # Make predictions on the test set
    predictions = model.predict(X_test)
    print(predictions[-1])

    # Implement your trading strategy based on the predicted values and technical indicators
    if predictions[-1] == 1:
        # Buy signal
        return TradeType.long.name
    else:
        # Sell signal
        return TradeType.short.name
