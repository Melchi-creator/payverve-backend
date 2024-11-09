from datetime import datetime, timedelta

import jwt

from ..config import secret_key


def generate_token(user_id):
        """ Generate a JWT token with an expiration time. """
        payload = {
            "user_id": user_id,
            "exp": datetime.utcnow() + timedelta(seconds=15)
        }
        return jwt.encode(payload=payload, key=secret_key)
    
    
def verify_token(token):
    """ Decode and verify JWT token """
    try:
        payload = jwt.decode(token, key=secret_key, algorithms=["HS256"])
        print(payload)
        return payload['user_id']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None