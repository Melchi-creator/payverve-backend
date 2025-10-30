"""
src/utilities/random_generator.py
This module provides a RandomGenerator class that contains static methods for generating various random identifiers.
It includes methods for generating wallet identifiers, swap reference numbers, Payverve transfer reference numbers,
and local transfer reference numbers.
"""

import secrets

from flask import jsonify


class RandomGenerator:
    """ RandomGenerator class provides static methods for generating random identifiers. """

    @staticmethod
    def wallet_identifier():
        """ Wallet Identifier Generator """

        try:
            randomiser = secrets.randbelow(10 ** 10)
            wallet_identifier = str(randomiser).zfill(10)
            return wallet_identifier

        except ArithmeticError:
            return jsonify({
                'code': 500,
                'status_message': 'arithmetic error',
                'message': 'could not generate wallet identifier'
            }), 500

        except RecursionError:
            return jsonify({
                'code': 500,
                'status_message': 'recursion error',
                'message': 'could not generate wallet identifier'
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
                'status_message': 'arithmetic error',
                'message': 'could not generate reference number'
            }), 500
        except RecursionError:
            return jsonify({
                'code': 500,
                'status_message': 'recursion error',
                'message': 'could not generate reference number'
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
                'status_message': 'arithmetic error',
                'message': 'could not generate reference number'
            }), 500
        except RecursionError:
            return jsonify({
                'code': 500,
                'status_message': 'recursion error',
                'message': 'could not generate reference number'
            }), 500

    @staticmethod
    def local_transfer_reference_number():
        """ Local Transfer Reference Number Generator """

        try:
            reference_number = secrets.token_hex(12)
            return reference_number
        except ArithmeticError:
            return jsonify({
                'code': 500,
                'status_message': 'arithmetic error',
                'message': 'could not generate reference number'
            }), 500
        except RecursionError:
            return jsonify({
                'code': 500,
                'status_message': 'recursion error',
                'message': 'could not generate reference number'
            }), 500
