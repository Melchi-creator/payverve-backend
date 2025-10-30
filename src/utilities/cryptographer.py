"""
src/utilities/cryptographer.py
This module contains the Cryptographer class, which is responsible for encrypting and decrypting status_messages.
It uses the cryptography library's Fernet symmetric encryption and supports key rotation.
"""
from cryptography.fernet import Fernet, InvalidToken, MultiFernet
from flask import jsonify

import config


class Cryptographer:
    """ this class is responsible for encrypting and decrypting status_messages """

    ferney_keys = MultiFernet([Fernet(config.fernet_key_one), Fernet(config.fernet_key_two)])

    @staticmethod
    def encrypt(status_message):
        """ this method encrypts a status_message """

        try:

            token = Cryptographer.ferney_keys.encrypt(str(status_message).encode()).decode('utf-8')

            return token

        except TypeError as e:
            return jsonify({
                "code": 500,
                'status_message': 'type error',
                'message': f'an incorrect datatype was inputted: {str(e)}',
            }), 500

    @staticmethod
    def decrypt(token):
        """ this method decrypts a token """

        try:

            status_message = Cryptographer.ferney_keys.decrypt(token).decode()

            return status_message

        except InvalidToken as e:
            rotate = Cryptographer.rotate(token)
            Cryptographer.decrypt(rotate)

            return jsonify({
                "code": 500,
                'status_message': 'invalid token',
                'message': f'incalid token: {str(e)}',
            }), 500

        except TypeError as e:
            return jsonify({
                "code": 500,
                'status_message': 'type error',
                'message': f'an incorrect datatype was inputted: {str(e)}',
            }), 500

        except Exception as e:
            return jsonify({
                "code": 500,
                'status_message': ' decryption error',
                'message': f'an error occurred during decryption: {str(e)}',
            }), 500

    @staticmethod
    def rotate(token):
        """ this method decrypts a token """

        try:

            status_message = Cryptographer.ferney_keys.rotate(token).decode()

            return status_message

        except InvalidToken as e:
            return jsonify({
                "code": 500,
                'status_message': 'invalid token',
                'message': f'incalid token: {str(e)}',
            }), 500
