"""
src/utilities/bearer_token.py
This module provides functions to encode and decode JWT tokens for authentication purposes.
"""

from datetime import datetime, timedelta, timezone


import jwt
from flask import request
from pytz import utc

import config


def encode_token(extra_payload: dict, jti: str, time_length, access_secret_key: str):
    """
    Generates the Auth Token
    """
    try:
        payload = {
            'exp': datetime.now(utc) + timedelta(days=0, seconds=time_length),
            'iat': datetime.now(utc),
            'nbf': datetime.now(utc),
            'jti': jti,
            'iss': request.url,
        }
        payload.update(extra_payload)
        token = jwt.encode(payload, access_secret_key, algorithm=config.algorithm)

        return token

    except Exception as e:
        return e


def decode_token(token, access_secret_key):
    """
    Decodes the authentication token
    :param access_secret_key:
    :param token:
    :return: integer|string
    """
    try:
        payload = jwt.decode(token, access_secret_key, algorithms=[config.algorithm])
        return payload
    except jwt.ExpiredSignatureError:
        return {"status": "expired"}
    except jwt.InvalidTokenError as e:
        return {"status": "invalid"}
