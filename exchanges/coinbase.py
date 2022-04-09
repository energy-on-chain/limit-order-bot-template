###############################################################################
# PROJECT: CVC Trading Bot
# AUTHOR: Matt Hartigan
# DATE: 21-Feb-2022
# FILENAME: coinbase.py
# DESCRIPTION: This file handles interface with the CVC CB prime account.
###############################################################################
import time
import datetime
import pytz
import json
import hmac
import codecs
import hashlib
import base64
import requests
from requests.auth import AuthBase
from google.cloud import storage
from google.cloud import secretmanager
from config import config_params


# CONFIG
client = secretmanager.SecretManagerServiceClient()    # get authentication info
project_id = "coherent-emblem-334620"

CB_PRIME_API_KEY = 'CVC_COINBASE_DARKICE_API_KEY'
CB_PRIME_PASSPHRASE = 'CVC_COINBASE_DARKICE_API_PASSPHRASE'
CB_PRIME_SECRET = 'CVC_COINBASE_DARKICE_API_SECRET'
cb_prime_api_key = client.access_secret_version({"name": f"projects/{project_id}/secrets/{CB_PRIME_API_KEY}/versions/latest"}).payload.data.decode('UTF-8')
cb_prime_passphrase = client.access_secret_version({"name": f"projects/{project_id}/secrets/{CB_PRIME_PASSPHRASE}/versions/latest"}).payload.data.decode('UTF-8')
cb_prime_secret= client.access_secret_version({"name": f"projects/{project_id}/secrets/{CB_PRIME_SECRET}/versions/latest"}).payload.data.decode('UTF-8')

api_url = 'https://api.exchange.coinbase.com/'
method = 'GET'
request_path = '/accounts'


# AUTHENTICATE
class CoinbaseExchangeAuth(AuthBase):
    def __init__(self, api_key, secret_key, passphrase):
        self.api_key = api_key
        self.secret_key = secret_key
        self.passphrase = passphrase

    def __call__(self, request):
        timestamp = str(int(time.time()))
        message = (timestamp + request.method + request.path_url).encode("utf-8")
        if request.body:
            message = b''.join([message, request.body]) 
        hmac_key = base64.b64decode(self.secret_key)
        signature = hmac.new(hmac_key, message, hashlib.sha256)
        signature_b64 = base64.b64encode(signature.digest())

        request.headers.update({
            'CB-ACCESS-SIGN': signature_b64,
            'CB-ACCESS-TIMESTAMP': timestamp,
            'CB-ACCESS-KEY': self.api_key,
            'CB-ACCESS-PASSPHRASE': self.passphrase,
        })
        return request


# FUNCTIONS
def get_coinbase_connection():
    return CoinbaseExchangeAuth(cb_prime_api_key, cb_prime_secret, cb_prime_passphrase)

def get_all_coinbase_accounts(auth):
    """ Prints a list of all accounts on the coinbase profile to screen so you can see 
    the balances. """
    response = requests.get(api_url + 'accounts', auth=auth)
    accounts = response.json()
    for account in accounts:
        print(account)

def get_single_coinbase_account(auth, account_id):
    """ Prints the avialable balance information for a specific coin account on the CB profile. """
    response = requests.get(api_url + 'accounts/' + account_id, auth=auth)
    return response.json()['balance']

def get_single_coinbase_account_ledger(auth, account_id):
    """ Returns the avialable ledger information for a specific coin account on the CB profile. """
    response = requests.get(api_url + 'accounts/' + account_id + '/ledger', auth=auth)
    return response.json()

def get_coinbase_fees_quote(auth):
    """ Prints the maker and taker fee rates for the account (depends on volume). """
    response = requests.get(api_url + 'fees', auth=auth)
    print(response.text)

def get_coinbase_btc_price_quote_coinbase(auth):
    """ Returns the current price of BTC. """
    response = requests.get(api_url + 'oracle', auth=auth)
    prices = response.json()['prices']
    return float(prices['BTC'])

def place_coinbase_market_order(auth, amount_usd, product_id, side, usd_acct, btc_acct):
    """ Places a market order on Coinbase. """
    print('Placing market ' + side + ' order on Coinbase...')
    print('Coinbase USD account balance before trade: ' + str(get_single_coinbase_account(auth, usd_acct)))
    print('Coinbase BTC account balance before trade: ' + str(get_single_coinbase_account(auth, btc_acct)))
    data = {
            'type': 'market',
            'side': side,
            'product_id': product_id,
            'funds': amount_usd,   # buy the amount dictated by config file (usd)
        }
    if config_params['in_production']:     
        response = requests.post(api_url + 'orders', auth=auth, json=data)
        return response.json()
    else:
        print('Not in production mode, no trade actually executed.')
        return ''

    print('Coinbase USD account balance after trade: ' + str(get_single_coinbase_account(auth, usd_acct)))
    print('Coinbase BTC account balance after trade: ' + str(get_single_coinbase_account(auth, btc_acct)))

def get_coinbase_trade_fees(auth, acct):
    """ Calculates fees for most recent Coinbase transaction in the given account. """
    print('Coinbase fee ledger for most recent trade executed:')

    current_time_str = datetime.datetime.now(tz=pytz.UTC).strftime("%Y-%m-%dT%H")
    fees = 0

    for item in get_single_account_ledger(auth, acct):
        if item['type'] == 'fee':
            time_fee_was_created_at = item['created_at'].split(':')[0]
            if time_fee_was_created_at == current_time_str:
                print(item)
                fees = fees + float(item['amount'])
    return fees
