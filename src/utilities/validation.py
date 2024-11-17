from datetime import datetime, timedelta

import jwt

from ..config import secret_key
from ..middlewares import NetworkDateTime


def generate_token(user_id, context=None):
        """ Generate a JWT token with an expiration time. """
        payload = {
            "user_id": user_id,
            "exp": NetworkDateTime.network_datetime() + timedelta(seconds=150),
            'context': context
        }
        return jwt.encode(payload=payload, key=secret_key)
    
    
def verify_token(token, context=None):
    """ Decode and verify JWT token """
    try:
        payload = jwt.decode(token, key=secret_key, algorithms=["HS256"])
        print(payload)
        
        if context and payload['context'] != context:
            raise jwt.InvalidTokenError
        
        return payload['user_id']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None