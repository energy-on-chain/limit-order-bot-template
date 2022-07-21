###############################################################################
# FILENAME: run.py
# PROJECT: EOC Limit Order Bot Template
# CLIENT: 
# AUTHOR: Matt Hartigan
# DATE: 8-Apr-2022
# FILENAME: config.py
# DESCRIPTION: Defines the key parameters for a given trading bot.
###############################################################################

config_params = {
    'name': 'EOC Limit Order Bot Template',
    'version': 'v0.1.0',    # maintain versioning based on https://semver.org/
    'in_production': False,
    'cloud_bucket_name': '',    # FIXME: add your value here
    'cloud_bucket_path': '',    # FIXME: add your value here
    'output_filename': '',     # FIXME: add your value here
    'bet': 10000,    # size of each bet in USD
    'threshold': 40000,    # price to take action at in usd
    # TODO: additional config parameters go here
}
