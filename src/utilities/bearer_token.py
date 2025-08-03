"""
src/utilities/bearer_token.py
This module provides functions to encode and decode JWT tokens for authentication purposes.
"""

from datetime import UTC, datetime, timedelta

import jwt
from flask import request

import config


def encode_token(extra_payload, time_length, secret_key):
    """
    Generates the Auth Token
    """
    try:
        payload = {
            'exp': datetime.now(UTC) + timedelta(days=0, seconds=time_length),
            'iat': datetime.now(UTC),
            'nbf': datetime.now(UTC),
            'iss': request.url,
        }
        payload.update(extra_payload)
        token = jwt.encode(payload, secret_key, algorithm=config.algorithm)
        return token
    except Exception as e:
        return e


def decode_token(token, secret_key):
    """
    Decodes the authentication token
    :param secret_key:
    :param token:
    :return: integer|string
    """
    try:
        payload = jwt.decode(token, secret_key, algorithms=[config.algorithm])
        return payload
    except jwt.ExpiredSignatureError:
        return {"status": "expired"}
    except jwt.InvalidTokenError:
        return {"status": "invalid"}
