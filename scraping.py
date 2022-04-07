from enums import *
from mw_requests.Request import Request

import requests

def get_historical(ticker, start_date, end_date, frequency=Frequency.daily):
    """
    """
    requests.get("https://www.marketwatch.com/investing/stock/aapl/download-data?startDate=7/7/2020&endDate=03/07/2022")

