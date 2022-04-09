###############################################################################
# PROJECT: CVC Auto-Ape Bot
# AUTHOR: Matt Hartigan
# DATE: 8-Apr-2022
# FILENAME: run.py
# DESCRIPTION: Runfile that instantiates the trading bot and executes it at a 
# user-defined frequency.
###############################################################################
import os
import time
import datetime
import requests
import schedule
import pandas as pd
import numpy as np
from google.cloud import storage
from exchanges.coinbase import get_coinbase_connection
from exchanges.falconx import get_falconx_connection
from bot import Bot
from config import config_params


# AUTHENTICATE 
if config_params['in_production']:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="credentials.json"


# FUNCTIONS
def alive():
    print('CVC Trading Bot #10 - "Auto-Ape Bot" - ' + config_params['version'] + ' is busy printing money... [' + str(datetime.datetime.utcnow()) + ']')


def run(bot):
    print(bot.name + ' ' + bot.version)
    print('Beginning run... [' + str(datetime.datetime.utcnow()) + ']')

    # Connect exchanges
    print('Connecting exchanges... [' + str(datetime.datetime.utcnow()) + ']')
    coinbase_connection = get_coinbase_connection()
    falconx_connection = get_falconx_connection()

    # Connect data and model file(s)
    print('Connecting data... [' + str(datetime.datetime.utcnow()) + ']')
    finage_df = pd.read_csv('gs://chainview-capital-dashboard-bucket-official/bots/bot_6/finage_ohlc_BTCUSD_60minute_fast.csv')    # price data
    history_df = pd.read_csv('gs://chainview-capital-dashboard-bucket-official/bots/bot_10/cvc_trading_bot10_results_log.csv')    # historical bot log file

   # Apply strategy
    print('Applying strategy... [' + str(datetime.datetime.utcnow()) + ']')
    strategy_result_df = bot.apply_strategy(
        history_df,
        finage_df,
    )

    # Execute trades
    print('Executing trades... [' + str(datetime.datetime.utcnow()) + ']')
    execute_trades_result_df = bot.execute_trades(
        strategy_result_df,
        coinbase_connection,
        falconx_connection,
        bot
    )

    # Evaluate performance
    print('Evaluating performance... [' + str(datetime.datetime.utcnow()) + ']')
    evaluate_performance_result_df = bot.evaluate_performance(
        execute_trades_result_df
    )


    # Output results
    print('Outputting results... [' + str(datetime.datetime.utcnow()) + ']')
    storage_client = storage.Client()
    bot.output_results(
        evaluate_performance_result_df,
        storage_client
    )
    print(bot.name + ' ' + bot.version + ' run complete.')


# ENTRY POINT
bot = Bot(config_params)
if config_params['in_production']:
    schedule.every(1).minutes.do(alive)    
    schedule.every().hour.at(":01").do(run, bot=bot)  
    while True:
        schedule.run_pending()
        time.sleep(1)
else:
    run(bot)


# TODO: 
# 
