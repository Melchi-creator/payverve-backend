"""
random_generator.py

Defines functions to generate random codes
"""

import secrets

from flask import jsonify


class RandomGenerator:
    """ This class defines random generators """

    @staticmethod
    def wallet_account_number():
        """ Wallet Account Number Generator """

        try:
            randomiser = secrets.randbelow(10 ** 10)
            account_number = str(randomiser).zfill(10)
            return account_number
        except ArithmeticError:
            return jsonify({
                'code': 500,
                'code_status': 'arithmetic error',
                'data': 'could not generate account number'
            }), 500
        except RecursionError:
            return jsonify({
                'code': 500,
                'code_status': 'recursion error',
                'data': 'could not generate account number'
            }), 500

    @staticmethod
    def swap_reference_number():
        """ Swap Reference Number Generator """

        try:
            reference_number = secrets.token_hex(8)
            return reference_number
        except ArithmeticError:
            return jsonify({
                'code': 500,
                'code_status': 'arithmetic error',
                'data': 'could not generate reference number'
            }), 500
        except RecursionError:
            return jsonify({
                'code': 500,
                'code_status': 'recursion error',
                'data': 'could not generate reference number'
            }), 500

    @staticmethod
    def payverve_transfer_reference_number():
        """ Payverve Transfer Reference Number Generator """

        try:
            reference_number = secrets.token_hex(10)
            return reference_number
        except ArithmeticError:
            return jsonify({
                'code': 500,
                'code_status': 'arithmetic error',
                'data': 'could not generate reference number'
            }), 500
        except RecursionError:
            return jsonify({
                'code': 500,
                'code_status': 'recursion error',
                'data': 'could not generate reference number'
            }), 500
