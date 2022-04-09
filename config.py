###############################################################################
# PROJECT: CVC Auto-Ape Bot
# AUTHOR: Matt Hartigan
# DATE: 8-Apr-2022
# FILENAME: config.py
# DESCRIPTION: Defines the key parameters for a given trading bot.
###############################################################################

config_params = {
    'name': 'Auto-Ape Bot',
    'version': 'v0.1.0',    # maintain versioning based on https://semver.org/
    'in_production': False,
    'cloud_bucket_name': 'chainview-capital-dashboard-bucket-official',
    'cloud_bucket_path': 'bots/',    # FIXME
    'output_filename': 'cvc_trading_bot10_results_log.csv',
    'bet': 1100,    # size of each bet in USD
    'threshold': 40000,    # price usd
    'coinbase_profile_id': '1268716e-4182-4820-95da-21f496a04f9f',    # 
    'coinbase_btc_account_id': '4e5cf952-a9e9-445c-9e95-2a4e5d74c566',    # ID for the dark ice coinbase acct
    'coinbase_usd_account_id': '13c8e547-1799-4d7f-8369-c6cf965e831a',      
    'coinbase_fee_estimate': 0.006,
    'coinbase_product_id': 'BTC-USD',
    # TODO: additional config parameters go here
}
