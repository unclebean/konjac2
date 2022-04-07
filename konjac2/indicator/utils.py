from enum import Enum


class TradeType(Enum):
    long = 0
    short = 1


class SignalCondition(Enum):
    crossing_up = 0
    crossing_down = 1
    moving_up = 2
    moving_down = 3


def is_crossing_up(source, target):
    return source > target


def is_crossing_down(source, target):
    return source < target
