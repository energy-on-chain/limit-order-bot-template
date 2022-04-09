###############################################################################
# PROJECT: CVC Auto-Ape Bot
# AUTHOR: Matt Hartigan
# DATE: 8-Apr-2022
# FILENAME: bot.py
# DESCRIPTION: Takes action based on user-defined indicator levels.
###############################################################################
import os
import time
import datetime
import pytz
import requests
import pandas as pd
import numpy as np
from exchanges.coinbase import get_all_coinbase_accounts, get_coinbase_btc_price_quote_coinbase, get_single_coinbase_account, get_single_coinbase_account_ledger, get_coinbase_fees_quote, get_coinbase_trade_fees
from exchanges.falconx import get_falconx_btc_price_quote, get_all_falconx_accounts, get_single_falconx_account_balance, get_falconx_token_pairs, place_falconx_market_order
from abc import ABC, abstractmethod
from base import BotInterface
from config import config_params


class Bot(BotInterface):

    def __init__(self, dictionary):
        for k, v in dictionary.items():
            setattr(self, k, v)

    def apply_strategy(self, historical_df, finage_df) -> pd.DataFrame:
        """ Apply the strategy logic. Returns df. """
        df = historical_df.copy()

        # Get previous trade and current trigger info
        trade_status = df['trade_status'].iloc[-1]    # get current trade status
        indicator = df['c'].iloc[-1]    # get current trade status FIXME
        action = ''

        # Evaluate trade case
        if indicator < config_params['threshold']:    # in trade zone when below threshold
            if trade_status == 'No Action':
                action = 'Buy'
            elif trade_status == 'Buy':
                action = 'Hold'
            elif trade_status == 'Sell':
                action = 'Buy'
            elif trade_status == 'Hold':
                action = 'Hold'
        else:    # not in trade zone
            if trade_status == 'No Action':
                action = 'No Action'
            elif trade_status == 'Buy':
                action = 'Sell'
            elif trade_status == 'Sell':
                action = 'No Action'
            elif trade_status == 'Hold':
                action = 'Sell'
        
        # Append row to bot history
        new_entry = finage_df.iloc[-1].to_list()
        new_entry.append(indicator)
        new_entry.append(action)
        new_entry.append(0.0)    # coinbase price placeholder
        new_entry.append(0.0)    # falconx price placeholder
        new_entry.append('TBD')    # exchange decision placeholder
        new_entry.append(0.0)    # capital_risked placeholder
        new_entry.append(0.0)    # running_capital_risked placeholder
        new_entry.append(0.0)    # coinbase usd
        new_entry.append(0.0)    # coinbase btc
        new_entry.append(0.0)    # coinbase usd fees
        new_entry.append(0.0)    # falconx usd
        new_entry.append(0.0)    # falconx btc
        new_entry.append(0.0)    # falconx usd fees
        new_entry.append(0.0)    # trade net profit
        new_entry.append(0.0)    # running net profits
        new_entry.append(0.0)    # trade raroi
        new_entry.append(0.0)    # running raroi
        new_entry.append(0.0)    # raw win loss
        new_entry.append(0.0)    # pure win loss
        df.loc[len(df)] = new_entry
        return df

    def execute_trades(self, strategy_result_df, coinbase_connection, falconx_connection, bot):
        """ Execute trades based on the result of applying strategy logic. Returns df. """

        # Get trade action that needs to be taken
        df = strategy_result_df.copy()
        trade_status = df['trade_status'].iloc[-1]    

        # Get price quotes
        coinbase_btc_quote = get_coinbase_btc_price_quote_coinbase(coinbase_connection)    # Coinbase (no fees)
        print('Coinbase base quote: ' + str(round(coinbase_btc_quote, 2)) + ' USD')
        coinbase_btc_quote_with_buy_fee = coinbase_btc_quote + config_params['coinbase_fee_estimate'] * coinbase_btc_quote
        coinbase_btc_quote_with_sell_fee = coinbase_btc_quote - config_params['coinbase_fee_estimate'] * coinbase_btc_quote
        print('Coinbase buy quote after adding ' + str(config_params['coinbase_fee_estimate'] * 100) + '% fee estimate: ' + str(round(coinbase_btc_quote_with_buy_fee, 2)) + ' USD')    # Coinbase (with fees)
        print('Coinbase sell quote after subtracting ' + str(config_params['coinbase_fee_estimate'] * 100) + '% fee estimate: ' + str(round(coinbase_btc_quote_with_sell_fee, 2)) + ' USD')    # Coinbase (with fees)
        falconx_quote = get_falconx_btc_price_quote(falconx_connection)    # FalconX
        falconx_btc_quote = falconx_quote[0]
        falconx_quote_id = falconx_quote[1]
        print('FalconX quote (includes basis point fee): ' + str(falconx_btc_quote) + ' USD')

        # Select best exchange for the desired trade action (i.e. buy low, sell high)
        if trade_status == 'Buy':    # buy low
            capital_risked = self.bet    # amount we are buying
            if coinbase_btc_quote_with_buy_fee < falconx_btc_quote:
                exchange_selected = 'Coinbase'
            else:
                exchange_selected = 'FalconX'
            print('The buy should be executed on: ' + exchange_selected)
        elif trade_status == 'Sell':    # sell high
            capital_risked = 0
            exchange_selected = df['exchange_selected'].iloc[-1]
            counter = 1
            while (exchange_selected == None) or (exchange_selected == 'None'):
                counter = counter + 1
                exchange_selected = df['exchange_selected'].iloc[-counter]
            print('The sell should be executed on: ' + exchange_selected)
        elif trade_status == 'Hold': 
            capital_risked = 0
            exchange_selected = 'None'
            print('No trade action should be taken, holding current open position.')
        else: 
            capital_risked = 0
            exchange_selected = 'None'
            print('No trade action should be taken, no position is currently open.')
            
        # Execute the trade on the desired exchange
        if exchange_selected == 'Coinbase' and trade_status == 'Buy':
            response = place_coinbase_market_order(coinbase_connection, self.bet, self.coinbase_product_id, 'buy', self.coinbase_usd_account_id, self.coinbase_btc_account_id)    # execute trade
            coinbase_usd_fees = get_coinbase_trade_fees(auth, self.coinbase_usd_account_id)    # calc usd fees
            falconx_usd_fees = 0
        elif exchange_selected == 'Coinbase' and trade_status == 'Sell':
            response = place_coinbase_market_order(coinbase_connection, self.bet, self.coinbase_product_id, 'sell', self.coinbase_usd_account_id, self.coinbase_btc_account_id)    # execute trade
            coinbase_usd_fees = get_coinbase_trade_fees(auth, self.coinbase_usd_account_id)    # calc usd fees
            falconx_usd_fees = 0
        elif exchange_selected == 'FalconX' and trade_status == 'Buy':
            response = place_falconx_market_order(falconx_connection, self.bet, ['BTC', 'USD'], 'buy')    
            falconx_usd_fees = response['fee_usd']
            coinbase_usd_fees = 0
        elif exchange_selected == 'FalconX' and trade_status == 'Sell':
            response = place_falconx_market_order(falconx_connection, self.bet, ['BTC', 'USD'], 'sell')   
            falconx_usd_fees = response['fee_usd']
            coinbase_usd_fees = 0
        else:    # HOLD and NO ACTION cases
            coinbase_usd_fees = 0
            falconx_usd_fees = 0
       
        # Log the trade action details
        df.at[len(df) - 1, 'coinbase_price'] = coinbase_btc_quote
        df.at[len(df) - 1, 'falconx_price'] = falconx_btc_quote
        df.at[len(df) -1 , 'exchange_selected'] = exchange_selected   
        df.at[len(df) -1 , 'capital_risked'] = capital_risked  
        df['running_capital_risked'] = df['capital_risked'].cumsum()
        df.at[len(df) -1 , 'coinbase_usd'] = get_single_coinbase_account(coinbase_connection, self.coinbase_usd_account_id)
        df.at[len(df) -1 , 'coinbase_btc'] = get_single_coinbase_account(coinbase_connection, self.coinbase_btc_account_id) 
        df.at[len(df) -1 , 'coinbase_usd_fees'] = coinbase_usd_fees
        df.at[len(df) -1 , 'falconx_usd'] = get_single_falconx_account_balance(falconx_connection, 'USD')
        df.at[len(df) -1 , 'falconx_btc'] = get_single_falconx_account_balance(falconx_connection, 'BTC')   
        df.at[len(df) -1 , 'falconx_usd_fees'] = falconx_usd_fees
        df.at[len(df) -1 , 'nofee_win_loss'] =  None    # this value will be changed as applicable during the evaluate_performance phase
        df.at[len(df) -1 , 'fee_win_loss'] = None    # this value will be changed as applicable during the evaluate_performance phase

        return df

    def evaluate_performance(self, input_df: pd.DataFrame) -> pd.DataFrame:
        """ Evaluate how the strategy is performing. Returns df. """
        df = input_df.copy()
        exchange_selected = df['exchange_selected'].iloc[-1]    # if trade action was taken, what exchange was it done on?

        # Calculate net profits at every "sell" instance by exchange
        df['coinbase_usd_shifted'] = df['coinbase_usd'].shift(periods=1)
        df['falconx_usd_shifted'] = df['falconx_usd'].shift(periods=1)
        df.loc[(df['trade_status'] == 'Sell') & (df['exchange_selected'] == 'Coinbase'), 'net_profit'] = pd.to_numeric(df['coinbase_usd']) - pd.to_numeric(df['coinbase_usd_shifted']) - self.bet    # account balance after sale - account balance before sale - original capital risked (fees are already accounted for in account balance)
        df.loc[(df['trade_status'] == 'Sell') & (df['exchange_selected'] == 'FalconX'), 'net_profit'] = pd.to_numeric(df['falconx_usd']) - pd.to_numeric(df['falconx_usd_shifted']) - self.bet    # account balance after sale - account balance before sale - original capital risked (fees are already accounted for in account balance)

        # Calculate remaining metrics based on net profits (e.g. raroi, running totals)
        df.loc[df['trade_status'] == 'Sell', 'raroi'] = pd.to_numeric(df['net_profit']) / self.bet    # net returns / original capital risked
        df['running_net_profit'] = df['net_profit'].cumsum()
        df['running_raroi'] = 0
        df['running_raroi'] = pd.to_numeric(df['running_net_profit']) / pd.to_numeric(df['running_capital_risked'])

        # Evaluate trades that were theoretical wins (i.e. not considering fees)
        df['nofee_win_loss'] = None    # default value
        df.loc[(df['trade_status'] == 'Sell') & (df['net_profit'] + df['coinbase_usd_fees'] + df['falconx_usd_fees'] > 0), 'nofee_win_loss'] = 'Win'
        df.loc[(df['trade_status'] == 'Sell') & (df['net_profit'] + df['coinbase_usd_fees'] + df['falconx_usd_fees'] < 0), 'nofee_win_loss'] = 'Loss'

        # Evaluate trades that were actual wins (i.e. considering fees)
        df['fee_win_loss'] = None    # defalut value
        df.loc[(df['trade_status'] == 'Sell') & (df['net_profit'] > 0), 'fee_win_loss'] = 'Win'
        df.loc[(df['trade_status'] == 'Sell') & (df['net_profit'] < 0), 'fee_win_loss'] = 'Loss'

        # Remove excess cols
        df = df.drop('coinbase_usd_shifted', axis=1)
        df = df.drop('falconx_usd_shifted', axis=1)
        return df
    
    def output_results(self, df, storage_client):
        """ Output bot performance / status for dashboarding and record keeping. Returns df. """
        bucket = storage_client.bucket(self.cloud_bucket_name)
        blob = bucket.blob(self.cloud_bucket_path + self.output_filename)
        local_filepath = '/tmp/' + self.output_filename
        df.to_csv(local_filepath, index=False)
        print('Final data frame written to output log on cloud: ')
        print(df)

        if config_params['in_production']:
            blob.upload_from_filename(local_filepath)    # write output file to cloud storage