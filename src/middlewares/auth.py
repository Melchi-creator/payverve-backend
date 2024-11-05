"""
auth.py

Defines functions for user authentication and authorization.
"""

from datetime import datetime, timedelta
from functools import wraps

import jwt
from flask import jsonify, make_response, request
from flask_login import LoginManager, login_user, logout_user

from .. import config
from ..models import AdminModel, UserModel

# from . import NetworkDateTime


class Auth:
    """ This class defines all auth funcions """
    
    SECRET_KEY = config.secret_key
    
    def __init__(self, app, db):
        self.login_manager = LoginManager()
        self.login_manager.init_app(app)
        
        self.db = db
        self.User = UserModel
        
        
        @self.login_manager.user_loader
        def load_user(user_id):
            user =  self.User.query.get(user_id)
            return user if user else AdminModel.query.get(user_id)
        
        
    def generate_token(self, user_id):
        """ Generate a JWT token with an expiration time. """
        payload = {
            "user_id": user_id,
            "exp": datetime.utcnow() + timedelta(minutes=12)
        }
        return jwt.encode(payload=payload, key=self.SECRET_KEY)
    
    
    def verify_token(self, token):
        """ Decode and verify JWT token """
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=["HS256"])
            return payload['user_id']
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
        
    
    def login(self, user: AdminModel | UserModel):
        """Authenticate user and set token in cookies if successful"""
        if user:
            token = self.generate_token(user.get_id())
            response = make_response(jsonify({"message": "Login succesful"}))
            response.set_cookie("auth_token", token)
            login_user(user=user)
            return response
        return jsonify({"error": "Invalid credentials"}), 401
    
    
    def logout(self):
        """ Clear the authentication cookie to log the user out."""
        response = make_response(jsonify({"message": "Logged out successfully"}))
        response.set_cookie("auth_token", "", expires=0)
        logout_user()
        return response
    
    
    def login_required(self, f):
        """Decorator to protect routes needing authentication. """
        @wraps(f)
        def decorated(*args, **kwargs):
            token = request.cookies.get('auth_token')
            if not token:
                return jsonify({"error": "Token is missing"}), 401
            
            user_id = self.verify_token(token)
            if not user_id:
                return jsonify({"error": "Token is invalid or expired!"}), 401
            kwargs['user_id'] = user_id
            return f(*args, **kwargs)
        return decorated
