"""
src/utilities/cryptographer.py
This module contains the Cryptographer class, which is responsible for encrypting and decrypting status_messages.
It uses the cryptography library's Fernet symmetric encryption and supports key rotation.
"""
from cryptography.fernet import Fernet, InvalidToken, MultiFernet

import config


class Cryptographer:
    """ this class is responsible for encrypting and decrypting status_messages """

    ferney_keys = MultiFernet(
        [Fernet(config.fernet_key_one), Fernet(config.fernet_key_two)])

    @staticmethod
    def encrypt(status_message):
        """ this method encrypts a status_message. Raises TypeError on bad input. """
        token = Cryptographer.ferney_keys.encrypt(
            str(status_message).encode()).decode('utf-8')
        return token

    @staticmethod
    def decrypt(token):
        """ this method decrypts a token. Raises InvalidToken/TypeError on failure. """
        status_message = Cryptographer.ferney_keys.decrypt(token).decode()
        return status_message

    @staticmethod
    def rotate(token):
        """ re-encrypts a token under the newest key. Raises InvalidToken on failure. """
        status_message = Cryptographer.ferney_keys.rotate(token).decode()
        return status_message
