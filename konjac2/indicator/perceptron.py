from sklearn.linear_model import Perceptron

from konjac2.indicator.logistic_regression import prepare_indicators_data


def trend_perceptron(candles, predict_step=0):
    data_y, data_x = prepare_indicators_data(candles)
    if predict_step == 0:
        train_x = data_x[1:]
        train_y = data_y[1:]
        test_x = data_x[-1:]
    else:
        train_x = data_x.shift(predict_step)[predict_step:]
        train_y = data_y[predict_step:]
        test_x = data_x[-predict_step:]
    clf = Perceptron(tol=1e-3, random_state=0)
    clf.fit(train_x[100:], train_y[100:])
    score = clf.score(train_x[100:], train_y[100:])
    return clf.predict(test_x), score
