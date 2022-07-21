###############################################################################
# PROJECT: EOC Limit Order Bot Template
# CLIENT: 
# AUTHOR: Matt Hartigan
# DATE: 8-Apr-2022
# FILENAME: README.txt
###############################################################################

// OVERVIEW


// REPO ARCHITECTURE
// exchanges/
Contains files that handle connection, authorization, etc. on individual exchanges.

// utils/
Contains common files that are used help build and evaluate different strategies.

// utils/indicators.py
A library of common trading chart indicators for use in strategy logic.

// utils/backtesting.py
A library of common spot and derivative backtesting functions that can be used
to quickly evaluate strategy performance and provide a common way of comparing
them to one another.

// base.py
Base (parent) class for trading bots. Acts as an interface.

// bot.py
Child clsas for individual trading bots. Implements the base.py interface.

// config.py
Strategy and bot-specific parameters are defined here (e.g. lookback periods, 
input file destinations, version number, etc.).

// run.py
Main runfile that defines how the bot runs (frequency, which functions, what
order, etc.).


###############################################################################
# CHANGELOG
###############################################################################
// v0.1.0
Initial release.

// v0.2.0
Coming soon...
