"""
src/middlewares/exchange_rate_api.py
This module defines the ExchangeRate class, which provides methods to fetch exchange rates
from an external API. It includes a method to get the exchange rate between two currencies.
It handles connection errors and returns appropriate JSON responses.
"""

import requests
from flask import jsonify, request

import config


class ExchangeRate:
    """ Exchange Rate Middleware"""

    @staticmethod
    def exchange_pair():
        """ Fetch exchange rate for a currency pair."""

        try:

            base_currency = request.json.get('base_currency')
            target_currency = request.json.get('target_currency')

            base_currency = base_currency.lower().strip()
            target_currency = target_currency.lower().strip()

            base_url = config.exchange_rate_api_url
            api_key = config.exchange_rate_api_key

            request_url = f'{base_url}/{api_key}/pair/{base_currency}/{target_currency}'

            response = requests.get(request_url)
            data = response.json()

            if data.get("result") == "success":
                conversion_rate = data.get("conversion_rate")

                return str(conversion_rate)

            return jsonify({
                'code': 500,
                'status_message': 'exchange failed',
                'message': f'Failed to fetch exchange rate for {base_currency} to {target_currency}'
            }), 500

        except ConnectionError as e:
            return jsonify({
                'code': 503,
                'status_message': 'exchange rate service unavailable',
                'message': str(e)
            }), 503

        except Exception as e:
            return jsonify({
                'code': 500,
                'status_message': 'interal server error',
                'message': str(e)
            }), 500
