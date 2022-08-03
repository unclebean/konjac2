"""
study("Normalized MACD",shorttitle='N MACD')
sma = input(12,title='Fast MA')
lma = input(21,title='Slow MA')
tsp = input(9,title='Trigger')
np = input(50,title='Normalize')
h=input(true,title='Histogram')
docol = input(false,title="Color Change")
dofill=input(false,title="Fill")
type = input(1,minval=1,maxval=3,title="1=Ema, 2=Wma, 3=Sma")

sh = type == 1 ? ema(close,sma)
 : type == 2 ? wma(close, sma)
 : sma(close, sma)

lon=type == 1 ? ema(close,lma)
 : type == 2 ? wma(close, lma)
 : sma(close, lma)

ratio = min(sh,lon)/max(sh,lon)
Mac = (iff(sh>lon,2-ratio,ratio)-1)
MacNorm = ((Mac-lowest(Mac, np)) /(highest(Mac, np)-lowest(Mac, np)+.000001)*2)- 1
MacNorm2 = iff(np<2,Mac,MacNorm)
Trigger = wma(MacNorm2, tsp)
Hist = (MacNorm2-Trigger)
Hist2 = Hist>1?1:Hist<-1?-1:Hist
swap=Hist2>Hist2[1]?green:red
swap2 = docol ? MacNorm2 > MacNorm2[1] ? #0094FF : #FF006E : red
plot(h?Hist2:na,color=swap,style=columns,title='Hist',histbase=0)
plot(MacNorm2,color=swap2,title='MacNorm')
plot(dofill?MacNorm2:na,color=MacNorm2>0?green:red,style=columns)
plot(Trigger,color=yellow,title='Trigger')
hline(0)
"""
import numpy as np
import pandas as pd
from pandas_ta import ema, wma


def n_macd(close, fast_length=13, slow_length=21, trigger_length=9, normalize=50):
    sh = ema(close, fast_length)
    lon = ema(close, slow_length)
    ratio = np.minimum(sh, lon) / np.maximum(sh, lon)
    mac = []
    for sh_v, lon_v, ratio_v in zip(sh, lon, ratio):
        if sh_v > lon_v:
            mac.append(2 - ratio_v - 1)
        else:
            mac.append(ratio_v - 1)
    mac = np.array(mac)
    rolling_mac = rolling_window(mac, normalize)

    rolling_mac_min = rolling_mac.min(1, initial=None)
    rolling_mac_min = rolling_mac_min[~np.isnan(rolling_mac_min)]
    rolling_mac_max = rolling_mac.max(1, initial=None)
    rolling_mac_max = rolling_mac_max[~np.isnan(rolling_mac_max)]

    offset = len(mac) - len(rolling_mac_min)
    mac_norm = ((mac[offset:] - rolling_mac_min) / (rolling_mac_max - rolling_mac_min + .000001) * 2) - 1
    trigger = wma(pd.Series(mac_norm), trigger_length)
    hist = mac_norm - trigger
    return list(trigger.values), list(mac_norm), list(hist)


def rolling_window(a, window_size):
    shape = (a.shape[0] - window_size + 1, window_size) + a.shape[1:]
    strides = (a.strides[0],) + a.strides
    return np.lib.stride_tricks.as_strided(a, shape=shape, strides=strides)
