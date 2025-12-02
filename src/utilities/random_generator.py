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
    def sim_account_number():
        """ Wallet Identifier Generator """

        try:
            randomiser = secrets.randbelow(10 ** 10)
            sim_account_number = str(randomiser).zfill(10)
            return sim_account_number

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

    @staticmethod
    def payverve_transfer_reference_number():
        """ Payverve Transfer Reference Number Generator """

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

    @staticmethod
    def foreign_transfer_reference_number():
        """ Foreign Transfer Reference Number Generator """

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

    @staticmethod
    def swift_code():
        """  """

        try:
            num = secrets.randbelow(999999 - 100 + 1) + 100

            return num

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
    def sim_external_ref():
        """  """

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
