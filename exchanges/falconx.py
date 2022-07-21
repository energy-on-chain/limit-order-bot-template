###############################################################################
# FILENAME: falconx.py
# PROJECT: EOC Limit Order Bot Template
# CLIENT: 
# AUTHOR: Matt Hartigan
# DATE: 21-Feb-2022
# FILENAME: falconx.py
# DESCRIPTION: This file handles interface with the FalconX API.
###############################################################################
import json
import hmac
import math
import hashlib
import time
import requests
import base64
from google.cloud import storage
from google.cloud import secretmanager
from requests.auth import AuthBase

from config import config_params


# CONFIG
client = secretmanager.SecretManagerServiceClient()    # get authentication info
project_id = ''    # FIXME: add your credentials here

FALCONX_API_KEY = ''    # FIXME: add your value here
FALCONX_PASSPHRASE = ''    # FIXME: add your value here
FALCONX_SECRET = ''    # FIXME: add your value here
falconx_api_key = client.access_secret_version({"name": f"projects/{project_id}/secrets/{FALCONX_API_KEY}/versions/latest"}).payload.data.decode('UTF-8')
falconx_passphrase = client.access_secret_version({"name": f"projects/{project_id}/secrets/{FALCONX_PASSPHRASE}/versions/latest"}).payload.data.decode('UTF-8')
falconx_secret= client.access_secret_version({"name": f"projects/{project_id}/secrets/{FALCONX_SECRET}/versions/latest"}).payload.data.decode('UTF-8')

api_url = 'https://api.falconx.io/v1/'


# AUTHENTICATE
class FXRfqAuth(AuthBase):
    def __init__(self, api_key, secret_key, passphrase):
        self.api_key = api_key
        self.secret_key = secret_key
        self.passphrase = passphrase

    def __call__(self, request):
        timestamp = str(time.time())
        request_body = request.body.decode() if request.body else ''
        message = timestamp + request.method + request.path_url + request_body
        hmac_key = base64.b64decode(self.secret_key)
        signature = hmac.new(hmac_key, message.encode(), hashlib.sha256)
        signature_b64 = base64.b64encode(signature.digest())

        request.headers.update({
            'FX-ACCESS-SIGN': signature_b64,
            'FX-ACCESS-TIMESTAMP': timestamp,
            'FX-ACCESS-KEY': self.api_key,
            'FX-ACCESS-PASSPHRASE': self.passphrase,
            'Content-Type': 'application/json'
        })
        return request


# FUNCTIONS
def get_falconx_connection():
    return FXRfqAuth(falconx_api_key, falconx_secret, falconx_passphrase)

def get_falconx_btc_price_quote(auth):
    """ Returns the current price of BTC. """
    params = {
        'token_pair': {
        'base_token': 'BTC',
        'quote_token': 'USD'
        },
        'quantity': {
        'token': 'BTC',
        'value': 1,
        },
        'side': 'buy'
    }
    r = requests.post(api_url + 'quotes', json=params, auth=auth)
    print('FalconX Quote details...')
    print('Buy price for 1 BTC: ' + str(r.json()['buy_price']))
    print('Gross fee bps: ' + str(r.json()['gross_fee_bps']))
    print('Gross fee usd: ' + str(r.json()['gross_fee_usd']))
    print('Rebate bps: ' + str(r.json()['rebate_bps']))
    print('Rebate usd: ' + str(r.json()['rebate_usd']))
    print('Fee bps: ' + str(r.json()['fee_bps']))
    print('Fee usd: ' + str(r.json()['fee_usd']))
    return [float(r.json()['buy_price']), r.json()['fx_quote_id']]

def get_all_falconx_accounts(auth):
    """ Prints the avialable balance information for a specific coin account on the FalconX profile. """
    response = requests.get(api_url + 'balances/total', auth=auth)
    return response.json()

def get_single_falconx_account_balance(auth, token):
    """ Returns the total balance on FalconX of thhe input token. """
    response = get_all_falconx_accounts(auth)
    for item in response:
        if item['token'] == token:
            return item['total_balance']
    
    print('Token balance for ' + token + ' not found on FalconX account, returning zero.')
    return 0

def get_falconx_token_pairs(auth):
    response = requests.get(api_url + 'pairs', auth=auth)
    return response.json()

def place_falconx_market_order(auth, amount_usd, product_id, side):
    """ Places a market order on FalconX. """
    print('Placing market ' + side + ' order on FalconX...')
    falconx_usd = get_single_falconx_account_balance(auth, 'USD')
    falconx_btc = get_single_falconx_account_balance(auth, 'BTC')
    print('FalconX USD account balance before trade: ' + str(falconx_usd))
    print('FalconX BTC account balance before trade: ' + str(falconx_btc))

    if side == 'buy':    # buy into a BTC position
        if falconx_usd <= 0:
            return 'There is a negative or zero balance in the FalconX account currently. No action taken.'
        else:
            token = 'BTC'
            side_for_falconx_api = 'buy'
            quote = get_falconx_btc_price_quote(auth)[0]
            value = round(amount_usd / quote, 8)

    elif side == 'sell':    # selling out of a BTC position into USD
        if falconx_btc <= 0:
            return 'There is a negative or zero BTC balance in the FalconX account currently. No action taken'
        else:
            token = 'BTC'
            side_for_falconx_api = 'sell'
            value = round_decimals_down(get_single_falconx_account_balance(auth, 'BTC'), 8)    # sell out of entire BTC position held in the account
    data = {
            "token_pair": {
                "base_token": product_id[0],
                "quote_token": product_id[1],
            },
            "quantity": {
                "token": token,
                "value": value,
            },
            "side": side_for_falconx_api,
            "order_type": "market",
        }

    if config_params['in_production']:     
        response = requests.post(api_url + 'order', auth=auth, json=data)
        print('FalconX USD account balance after trade: ' + str(get_single_falconx_account_balance(auth, 'USD')))
        print('FalconX BTC account balance after trade: ' + str(get_single_falconx_account_balance(auth, 'BTC')))
        return response.json()
    else:
        print('Not in production mode, no trade actually executed.')
        return 'Not in production mode, no trade actually executed.'

def round_decimals_down(number, decimals):
    """ Returns a value rounded down to a specific number of decimal places. """
    if not isinstance(decimals, int):
        raise TypeError("decimal places must be an integer")
    elif decimals < 0:
        raise ValueError("decimal places has to be 0 or more")
    elif decimals == 0:
        return math.floor(number)

    factor = 10 ** decimals
    return math.floor(number * factor) / factor
