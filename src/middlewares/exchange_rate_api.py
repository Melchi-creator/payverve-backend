"""
exchange_rate_api.py

Defines a function to fetch currencies exchange rate
data from https://exchangerate-api.com
"""

import requests

import config


class ExchangeRate:
    """ Defines functions for internet time date """

    @staticmethod
    def exchange_pair(base_currency, target_currency):
        """ Fetches datetime from the internet """

        try:

            base_url = config.exchange_rate_api_url
            api_key = config.exchange_rate_api_key

            request_url = f'{base_url}/{api_key}/pair/{base_currency}/{target_currency}'

            response = requests.get(request_url)
            data = response.json()

            return data

        except ConnectionError:
            return
