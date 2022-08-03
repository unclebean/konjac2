def moving_average(close, length=13):
    windows = close.rolling(length)
    moving_averages = windows.mean()
    moving_averages_list = moving_averages.tolist()

    return moving_averages_list[length - 1:]