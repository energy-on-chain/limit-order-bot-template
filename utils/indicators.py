###############################################################################
# PROJECT: CVC Trading Bot
# AUTHOR: Matt Hartigan
# DATE: 4-Jan-2022
# FILENAME: indicators.py
# DESCRIPTION: Library of indicator functions for CVC trading bots.
###############################################################################
import statistics
import pandas as pd
import numpy as np


def bollinger_bands(df, label, period, sd):
    """ Classic bollinger band function. Takes in data frame, selects the input
    price data column based on the input label parameter, then calculates the
    SMA for the specified lookback period as well as standard deviation. 
    Returns a dictionary with the price, top, mid, and bottom band values."""

    results_list = []
    counter = 0
    while counter < len(df[label]):
        if counter < period:
            bb_mid = None
            bb_top = None
            bb_bot = None
        else:
            data_slice = list(df.iloc[(counter - period):counter, df.columns.get_loc(label)])
            bb_mid = statistics.mean(data_slice)
            std = statistics.pstdev(data_slice)
            bb_top = bb_mid + (sd * std)
            bb_bot = bb_mid - (sd * std)

        results_list.append([bb_top, bb_mid, bb_bot])
        counter = counter + 1

    result_df = pd.DataFrame(results_list, columns=['bb_top', 'bb_mid', 'bb_bot'])
    return result_df


def cci(input_df, high, low, close, lookback, cci_factor):
    """ Classic commodity channel index (CCI) indicator. 

    CCI = (Typical Price - Moving Average) / (CCI Factor * Mean Deviation)

    ...where Typical Price = (High + Low + Close) / 3
    ...and where Moving Average = 

    source: https://www.investopedia.com/terms/c/commoditychannelindex.asp
    """
    df = input_df.copy()

    df['typical_price'] = (df[high] + df[low] + df[close]) / 3    # calc typical price
    df['sma'] = df['typical_price'].rolling(lookback).mean()

    mad = lambda x: np.fabs(x - x.mean()).mean()
    df['mad'] = df['typical_price'].rolling(lookback).apply(mad, raw=True)
    df['cci'] = (df['typical_price'] - df['sma']) / (cci_factor * df['mad'])

    return df['rsi']


def rsi(input_df, lookback):
    """ Classic relative strength index (RSI) indicator. 
    
        source: https://www.macroption.com/rsi-calculation/
    """
    df = input_df.copy()

    df['close_shift'] = df['c'].shift(periods=1)    # find ups and downs
    df['ups'] = np.where((df['c'] - df['close_shift']) > 0, abs(df['c'] - df['close_shift']), 0)
    df['downs'] = np.where((df['c'] - df['close_shift']) < 0, abs(df['c'] - df['close_shift']), 0)

    up_string = 'rolling_ups_' + str(lookback) +'sma'    # col labels
    down_string = 'rolling_downs_' + str(lookback) +'sma'

    df[up_string] = df['ups'].rolling(window=lookback).mean()    # calc avgs
    df[down_string] = df['downs'].rolling(window=lookback).mean()

    df['rs'] = df[up_string] / df[down_string]

    df['rsi'] = 100 - (100 / (1 + df['rs']))

    return df
