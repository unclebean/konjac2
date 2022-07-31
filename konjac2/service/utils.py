from datetime import datetime


def get_nearest_complete_h4_hour():
    current_hour = datetime.utcnow().hour - 1
    if current_hour < 4:
        return 0
    elif current_hour < 8:
        return 4
    elif current_hour < 12:
        return 8
    elif current_hour < 16:
        return 12
    elif current_hour < 20:
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
    complete_hour = get_nearest_complete_h4_hour()
    last_index_hour = h4_data.index[-1].hour
    if last_index_hour > complete_hour:
        return h4_data[:-1]
    return h4_data

