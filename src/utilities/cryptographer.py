"""
src/utilities/cryptographer.py
This module contains the Cryptographer class, which is responsible for encrypting and decrypting messages.
It uses the cryptography library's Fernet symmetric encryption and supports key rotation.
"""
from cryptography.fernet import Fernet, InvalidToken, MultiFernet
from flask import jsonify

import config


class Cryptographer:
    """ this class is responsible for encrypting and decrypting messages """

    ferney_keys = MultiFernet([Fernet(config.fernet_key_one), Fernet(config.fernet_key_two)])

    @staticmethod
    def encrypt(message):
        """ this method encrypts a message """

        try:

            token = Cryptographer.ferney_keys.encrypt(str(message).encode()).decode('utf-8')

            return token

        except TypeError as e:
            return jsonify({
                "code": 500,
                'code_message': 'type error',
                'data': f'an incorrect datatype was inputted: {str(e)}',
            }), 500

    @staticmethod
    def decrypt(token):
        """ this method decrypts a token """

        try:

            message = Cryptographer.ferney_keys.decrypt(token).decode()

            return message

        except InvalidToken as e:
            rotate = Cryptographer.rotate(token)
            Cryptographer.decrypt(rotate)

            return jsonify({
                "code": 500,
                'code_message': 'invalid token',
                'data': f'incalid token: {str(e)}',
            }), 500

        except TypeError as e:
            return jsonify({
                "code": 500,
                'code_message': 'type error',
                'data': f'an incorrect datatype was inputted: {str(e)}',
            }), 500

        except Exception as e:
            return jsonify({
                "code": 500,
                'code_message': ' decryption error',
                'data': f'an error occurred during decryption: {str(e)}',
            }), 500

    @staticmethod
    def rotate(token):
        """ this method decrypts a token """

        try:

            message = Cryptographer.ferney_keys.rotate(token).decode()

            return message

        except InvalidToken as e:
            return jsonify({
                "code": 500,
                'code_message': 'invalid token',
                'data': f'incalid token: {str(e)}',
            }), 500
