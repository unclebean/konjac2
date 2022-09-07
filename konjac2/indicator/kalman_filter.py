import numpy as np
import pandas as pd
from pykalman import KalmanFilter


def kalman_candles(candles):
    kf = KalmanFilter(transition_matrices=[1], observation_matrices=[1], initial_state_mean=0,
                      initial_state_covariance=1, observation_covariance=1, transition_covariance=0.01)
    open_means, _ = kf.filter(candles.open)
    low_means, _ = kf.filter(candles.low)
    high_means, _ = kf.filter(candles.high)
    close_means, _ = kf.filter(candles.close)
    return pd.DataFrame(
        {
            "open": np.ravel(open_means),
            "low": np.ravel(low_means),
            "high": np.ravel(high_means),
            "close": np.ravel(close_means),
            "volume": candles.volume
        },
        index=candles.index
    )
