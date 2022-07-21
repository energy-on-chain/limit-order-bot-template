###############################################################################
# FILENAME: indicators.py
# PROJECT: EOC Limit Order Bot Template
# CLIENT: 
# AUTHOR: Matt Hartigan
# DATE CREATED: 31 May 2022
# DESCRIPTION: Library of indicator functions for EOC trading bots.
###############################################################################
import os
import math
import statistics
import pandas as pd
import numpy as np


# GENERAL INDICATORS
def bollinger_band(input_df, column_label, rolling_window, standard_deviation):
    """ Classic bollinger band width calculation. Takes an input pandas data 
    frame, computes the bollinger band width for the input column at the input
    rolling window using the input standard deviation, then returns the original
    input data frame with the bollinger band results columns appended. """

    df = input_df.copy()    # make copy of input df

    df['std'] = df[column_label].rolling(rolling_window).std()    # calc rolling standard deviation

    col_name = str(rolling_window) + '__BBands'    # define output column name

    df['bb_mid'] = df[column_label].rolling(rolling_window).mean()    # calculate rolling mean (BB midpoint)
    df['bb_top'] = df['bb_mid'] + (standard_deviation * df['std'])    # create top band    
    df['bb_bot'] = df['bb_mid'] - (standard_deviation * df['std'])    # create bottom band
    df[col_name] = (df['bb_top'] - df['bb_bot']) / df['bb_mid']    # calculate (normalized) width

    df.drop('std', axis=1, inplace=True)    # drop unnecessary columns from output
    df.drop('bb_mid', axis=1, inplace=True)    
    df.drop('bb_top', axis=1, inplace=True)    
    df.drop('bb_bot', axis=1, inplace=True)    
    
    return df


def roc(input_df, close_label, rolling_window):
    """ Classic rate of change calculation. 
    Formula for the input "rolling_window" lookback period:
    ROC = (original_close - current_close) / original_close
    
    Returns the original data frame with the result appended as a new column. """

    df = input_df.copy()

    df['previous_price'] = df[close_label].shift(rolling_window - 1)
    df['price_change'] = df[close_label] - df['previous_price']    # price change over specified lookback period
    col_name = str(rolling_window) + ' _ROC'
    df[col_name] = df['price_change'] / df['previous_price']    # raw price change (positive or negative)

    df.drop('price_change', axis=1, inplace=True)    # drop unnecessary columns from output
    df.drop('previous_price', axis=1, inplace=True)

    return df


# MOVING AVERAGES
def sma(input_df, close_label, rolling_window):
    """ Classic simple moving average calculation. Takes an input pandas data frame,
    computes the simple average of the last "rolling_window" periods, then returns the
    original data frame with the output appended as a new column. """

    df = input_df.copy()

    col_name = str(rolling_window) + ' _SMA'
    df[col_name] = df[close_label].rolling(rolling_window).mean()

    return df


def zlema(input_df, close_label, rolling_window):
    """ Zero Lag Exponential Moving Average. This is a variation of EMA which adds a momentum term to
    reduce lag in the average in order to track current prices more closely. 
    
    Formula Source: https://tulipindicators.org/zlema
    """

    df = input_df.copy()

    lag = int(math.floor((rolling_window - 1) / 2))    # calc lag factor
    smoothing_factor = 2 / (rolling_window + 1)    # calc smoothing factor

    # calc ema
    df['ema'] = df[close_label].rolling(window=rolling_window, min_periods=rolling_window).mean()[:rolling_window+1]    # get regular sma to start
    for i, row in enumerate(df['ema'].iloc[rolling_window+1:]):    # calculate ema based on first cell with sma
        df['ema'].iloc[i + rolling_window + 1] = ((df[close_label].iloc[i + rolling_window + 1] - df['ema'].iloc[i + rolling_window]) * smoothing_factor) + df['ema'].iloc[i + rolling_window]

    # calc zlema
    col_name = str(rolling_window) + '__ZLEMA'
    df[col_name] = None
    df[col_name].iloc[lag - 1] = df[close_label].iloc[lag - 1]    # get close price of the lagged day to start the zlema column calc from
    for i, row in enumerate(df[col_name].iloc[lag:]):    
        df[col_name].iloc[i + lag] = ((1- smoothing_factor) * df[col_name].iloc[i + lag - 1]) + smoothing_factor * (df[close_label].iloc[i + lag] + (df[close_label].iloc[i + lag] - df[close_label].iloc[i + lag - lag]))    # apply formula

    return df


# MOMENTUM INDICATORS
def momentum(input_df, close_label, rolling_window):
    """ Measures the speed of price changes in an asset which can indicate trend.
    Formula:
    
    Momentum = current_price - price_n_periods_ago
    Source: https://www.investopedia.com/articles/technical/081501.asp#:~:text=Market%20momentum%20is%20measured%20by,plotted%20around%20a%20zero%20line.
    """

    df = input_df.copy()

    col_name = str(rolling_window) + ' _momentum'
    df[col_name] = df[close_label] - df[close_label].shift(periods=rolling_window-1)

    return df


def cci(input_df, high_label, low_label, close_label, rolling_window):
    """ Classic commodity channel index (CCI) indicator. CCI is a momentum based oscillator that
    is used to help assess whether an asset is overbought or oversold. This function takes an 
    input pandas data frame, computes rolling CCI based on the given input values, then returns the
    original input data frame with the cci value column appended.
    
    Formula:
    CCI = (Typical Price - Moving Average) / (CCI Factor * Mean Deviation)
    ...where Typical Price = (High + Low + Close) / 3
    source: https://www.investopedia.com/terms/c/commoditychannelindex.asp
    """

    df = input_df.copy()    # make copy of input df

    lambert_constant = 0.015

    df['typical_price'] = (df[high_label] + df[low_label] + df[close_label]) / 3    # calculate typical price
    df['typical_price_sma'] = df['typical_price'].rolling(rolling_window).mean()    # calculate typical price rolling sma

    for x in range(0, rolling_window):    # add a shifted typical price column for each sma period
        col_name = 'tp_shift_' + str(x)
        df[col_name] = df['typical_price'].shift(periods=x) 
        df = df.copy()    # avoid fragmentation

    df['mean_deviation'] = 0    # initialize mean_deviation col
    for x in range(0, rolling_window):    # sum the abs difference between sma and prev [rolling window] typical prices
        col_name = 'tp_shift_' + str(x)
        df['mean_deviation'] = df['mean_deviation'] + abs(df['typical_price_sma'] - df[col_name])

    df['mean_deviation_adj'] = df['mean_deviation'] / rolling_window    # normalize by size of rolling window

    col_name = str(rolling_window) + '__CCI'
    df[col_name] = (df['typical_price'] - df['typical_price_sma']) / (lambert_constant * df['mean_deviation_adj'])    # calculate cci

    df.drop('typical_price', axis=1, inplace=True)    # drop unnecessary columns from output
    df.drop('typical_price_sma', axis=1, inplace=True)
    df.drop('mean_deviation', axis=1, inplace=True)
    df.drop('mean_deviation_adj', axis=1, inplace=True)
    for x in range(0, rolling_window):    
        col_name = 'tp_shift_' + str(x)
        df.drop(col_name, axis=1, inplace=True) 

    return df


def rsi(input_df, close_label, rolling_window):
    """ Classic Wilder's relative strength index (RSI) indicator. Measures the momentum of an asset by comparing
    how quickly people are bidding the price up or down. 30 is typically considered oversold, 70 is typically 
    considered overbought.
    
        source: https://www.alpharithms.com/relative-strength-index-rsi-in-python-470209/
        source: https://school.stockcharts.com/doku.php?id=technical_indicators:relative_strength_index_rsi
    """
    df = input_df.copy()

    df['previous_close'] = df[close_label].shift(periods=1)    # calcluate price change
    df['change'] = df[close_label] - df['previous_close']

    df['gain'] = df['change'].clip(lower=0)
    df['loss'] = abs(df['change'].clip(upper=0))

    df['avg_gain'] = df['gain'].rolling(window=rolling_window, min_periods=rolling_window).mean()[:rolling_window+1]    # get regular sma for gains
    df['avg_loss'] = df['loss'].rolling(window=rolling_window, min_periods=rolling_window).mean()[:rolling_window+1]    # get regular sma for losses

    for i, row in enumerate(df['avg_gain'].iloc[rolling_window+1:]):    # calculate Wilder-method-specific moving averages
        df['avg_gain'].iloc[i + rolling_window + 1] = (df['avg_gain'].iloc[i + rolling_window] * (rolling_window - 1) + df['gain'].iloc[i + rolling_window + 1]) / rolling_window

    for i, row in enumerate(df['avg_loss'].iloc[rolling_window+1:]):    # calculate Wilder-method-specific moving averages
        df['avg_loss'].iloc[i + rolling_window + 1] = (df['avg_loss'].iloc[i + rolling_window] * (rolling_window - 1) + df['loss'].iloc[i + rolling_window + 1]) / rolling_window

    df['rs'] = df['avg_gain'] / df['avg_loss']    # calculate rs

    col_name = str(rolling_window) + ' _RSI'
    df[col_name] = 100 - (100 / (1 + df['rs']))    # calculate rsi

    df.drop('previous_close', axis=1, inplace=True)    # drop unnecessary columns from output
    df.drop('change', axis=1, inplace=True)
    df.drop('gain', axis=1, inplace=True)
    df.drop('loss', axis=1, inplace=True)
    df.drop('avg_gain', axis=1, inplace=True)
    df.drop('avg_loss', axis=1, inplace=True)
    df.drop('rs', axis=1, inplace=True)

    return df


def money_flow_index(input_df, close_label, high_label, low_label, volume_label, rolling_window):
    """ Movement indicator that analyzes both time and price to measure trading pressure in either 
    direction. Also called volume-weighted rsi since it includes volume, unlike traditional rsi which
    only includes price. A reading above 80 is considered overbought and a reading below 20 is considered
    oversold. 
    
    Source: https://corporatefinanceinstitute.com/resources/knowledge/trading-investing/money-flow-index/
    """

    df = input_df.copy()

    df['typical_price'] = ((df[close_label] + df[high_label] + df[low_label]) / 3)

    df['change'] = df['typical_price'] - df['typical_price'].shift(periods=1)
    df['raw_money_flow'] = df[volume_label] * df['typical_price']
    df['positive_flow'] = 0
    df['negative_flow'] = 0
    df.loc[df['change'] >= 0, 'positive_flow'] = df['raw_money_flow']
    df.loc[df['change'] < 0, 'negative_flow'] = df['raw_money_flow']
    df['sum_positive_money_flows'] = df['positive_flow'].rolling(rolling_window).sum()    
    df['sum_negative_money_flows'] = df['negative_flow'].rolling(rolling_window).sum()
    df['money_flow_ratio'] = df['sum_positive_money_flows'] / df['sum_negative_money_flows']

    col_name = str(rolling_window) + '__MFI'   
    df[col_name] = 100 - (100 / (1 + df['money_flow_ratio']))

    df.drop('typical_price', axis=1, inplace=True)    # drop unnecessary columns from output
    df.drop('change', axis=1, inplace=True)    
    df.drop('raw_money_flow', axis=1, inplace=True)    
    df.drop('positive_flow', axis=1, inplace=True)    
    df.drop('negative_flow', axis=1, inplace=True)    
    df.drop('sum_positive_money_flows', axis=1, inplace=True)    
    df.drop('sum_negative_money_flows', axis=1, inplace=True)    
    df.drop('money_flow_ratio', axis=1, inplace=True)    

    return df


def chande_momentum_oscillator(input_df, close_label, rolling_window):
    """ This is a momentum indicator that calculates the difference between recent gains and 
    recent losses to give a sense of relative strength or weakness of a market. These kinds
    of indicators are typically less effective in strongly trending markets, and they are 
    also typically more effective when used as part of pattern recognition instead of absolute 
    levels. 
    
    Formula (over a given "rolling_window" lookback period):
    CMO = [(sum_higher_closes - sum_lower_closes) / (sum_higher_closes + sum_lower_closes)] x 100
    Source: https://www.investopedia.com/terms/c/chandemomentumoscillator.asp, https://tulipindicators.org/cmo
    """

    df = input_df.copy()

    # sum when closes are higher and when they are lower
    df['change'] = df[close_label] - df[close_label].shift(periods=1)
    df['higher_closes'] = 0
    df['lower_closes'] = 0
    df.loc[df['change'] >= 0, 'higher_closes'] = abs(df['change'])
    df.loc[df['change'] < 0, 'lower_closes'] = abs(df['change'])
    df['sum_higher_closes'] = df['higher_closes'].rolling(rolling_window).sum()    
    df['sum_lower_closes'] = df['lower_closes'].rolling(rolling_window).sum()

    # calculate rolling metric
    col_name = str(rolling_window) + ' _CMO'   
    df[col_name] = ((df['sum_higher_closes'] - df['sum_lower_closes']) / (df['sum_higher_closes'] + df['sum_lower_closes'])) * 100

    df.drop('change', axis=1, inplace=True)    # drop unnecessary columns from output
    df.drop('higher_closes', axis=1, inplace=True)    
    df.drop('lower_closes', axis=1, inplace=True)    
    df.drop('sum_higher_closes', axis=1, inplace=True)    
    df.drop('sum_lower_closes', axis=1, inplace=True)    

    return df


# VOLATILITY INDICATORS
def annualized_historical_volatility(input_df, close_label, rolling_window):
    """ Annualized, historical, "close to close" volatility calculation. Other options are parkinson and garman klass vol.
    Note that this volatility calc assumes 365 periods (aka days) occur in a given financial year 
    since crypto trades 24/7. Adjust the "FIXME" comments accordingly if you want to use a tradfi-type calc. 
    Source: https://www.macroption.com/historical-volatility-excel/
    """

    df = input_df.copy()

    annualized_factor = 365    # num periods in a year (crypto)
    # annualized_factor = 252    # FIXME: num periods in a year (tradfi)

    df['close_shift'] = df[close_label].shift(periods=1)    # shift close periods by 1 for calc on following line 
    # df['interday_returns'] = (df[close_label] / df['close_shift']) - 1    # FIXME: traditional way to find inter-period percent return (can switch with ln method)
    df['interday_returns'] = np.log(df[close_label] / df['close_shift'])
    df['std'] = df['interday_returns'].rolling(rolling_window).std()    # calc standard dev
    col_name = str(rolling_window) + '__volatility'   
    df[col_name] = math.sqrt(annualized_factor) * df['std']    # annualize to get result

    df.drop('std', axis=1, inplace=True)    # drop unnecessary columns from output
    df.drop('interday_returns', axis=1, inplace=True)    
    df.drop('close_shift', axis=1, inplace=True)    

    return df


def garman_klass_volatility(input_df, open_label, high_label, low_label, close_label, rolling_window):
    """ Another measure of volatility (e.g. close/close volatility, parkinson volatility, etc.)
    that looks to improve accuracy by taking into account information beyond just the close price.
    
    Source: https://www.youtube.com/watch?v=_v1UHy7OpjU
    """
    
    df = input_df.copy()

    constant = (2 * np.log(2)) - 1    # the constant for the second term in the equation

    # calculate component terms
    df['ln(h/l)_squared'] = ((np.log(df[high_label] / df[low_label])) ** 2)    # first term in equation
    df['ln(c/o)_squared'] = (np.log(df[close_label] / df[open_label])) ** 2    # second term in equation

    # weight component terms
    df['combined_terms'] = (0.5 * df['ln(h/l)_squared']) + (constant * df['ln(c/o)_squared'])
    
    # calc rolling indicator
    col_name = str(rolling_window) + '__garman.klass'   
    df[col_name] = df['combined_terms'].rolling(rolling_window).mean()    # sum gk terms
    df[col_name] = np.sqrt(df[col_name])    # take sqrt

    df.drop('ln(h/l)_squared', axis=1, inplace=True)    # drop unnecessary columns from output
    df.drop('ln(c/o)_squared', axis=1, inplace=True)    
    df.drop('combined_terms', axis=1, inplace=True)    

    return df


# PRICE INDICATORS
def vwap(input_df, close_label, high_label, low_label, volume_label, rolling_window):
    """ Classive volume weighted average price calculation.
    
    Formula for a given "rolling_window" lookback period:
    
    VWAP = (typical_price * volume) / cumulative_volume
    ...where typical_price = (high + low + close) / 3
    """

    df = input_df.copy()

    df['typical_price'] = ((df[close_label] + df[high_label] + df[low_label]) / 3)
    df['volume_times_price'] = df[volume_label] * df['typical_price']
    df['cumulative_volume'] = df[volume_label].rolling(rolling_window).sum()
    col_name = str(rolling_window) + '__VWAP'
    df[col_name] = df['volume_times_price'] / df['cumulative_volume']

    df.drop('typical_price', axis=1, inplace=True)    # drop unnecessary columns from output
    df.drop('volume_times_price', axis=1, inplace=True)    
    df.drop('cumulative_volume', axis=1, inplace=True)    

    return df

