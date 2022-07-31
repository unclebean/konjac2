from datetime import datetime


def get_nearest_complete_h4_hour():
    current_hour = datetime.utcnow().hour - 1
    if 4 <= current_hour < 8:
        return 0
    elif 8 <= current_hour < 12:
        return 4
    elif 12 <= current_hour < 16:
        return 8
    elif 16 <= current_hour < 20:
        return 12
    elif 20 <= current_hour <= 23:
        return 16
    else:
        return 20


def filter_incomplete_h1_data(h1_data):
    current_hour = datetime.utcnow().hour
    last_index_hour = h1_data.index[-1].hour
    if last_index_hour < current_hour:
        return h1_data
    return h1_data[:-1]


def filter_incomplete_h4_data(h4_data):
    return h4_data

