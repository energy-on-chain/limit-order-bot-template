###############################################################################
# PROJECT: CVC Trading Bot Template
# AUTHOR: Matt Hartigan
# DATE: 25-Feb-2022
# FILENAME: base.py
# DESCRIPTION: Base file that defines the interface for CVC trading bots.
###############################################################################
import os
import time
import datetime
import requests
import pandas as pd
import numpy as np
from abc import ABC, abstractmethod


class BotInterface(ABC):

    @abstractmethod
    def __init__(self, dictionary: dict):
        pass

    @abstractmethod
    def apply_strategy(self):
        """ Apply the strategy logic. Returns df. """
        pass

    @abstractmethod
    def execute_trades(self):
        """ Execute trades based on the result of applying strategy logic. Returns df. """
        pass

    @abstractmethod
    def evaluate_performance(self, df: pd.DataFrame) -> pd.DataFrame:
        """ Evaluate how the strategy is performing. Returns df. """
        pass
    
    @abstractmethod
    def output_results(self):
        """ Output bot performance / status for dashboarding and record keeping. Returns df. """
        pass
