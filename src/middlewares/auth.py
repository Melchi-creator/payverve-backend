# """
# auth.py
#
# Defines functions for user authentication and authorization.
# """
#
# from datetime import timedelta
# from functools import wraps
#
# import jwt
# from flask import jsonify, make_response, render_template, request
# from flask_login import LoginManager, login_user, logout_user
#
# from .. import config
# from ..middlewares import NetworkDateTime
# from ..middlewares.location import login_device_info
# from ..models import AdminModel, UserModel
# from ..utilities import emailHandler
#
#
# class Auth:
#     """ This class defines all auth funcions """
#
#     SECRET_KEY = config.secret_key
#     __instance = None
#
#
#     def __new__(cls, *args, **kwargs):
#         if cls.__instance is None:
#             cls.__instance = super(Auth, cls).__new__(cls)
#         return cls.__instance
#
#
#     def init_app(self, app=None, db=None):
#         self.login_manager = LoginManager()
#         self.login_manager.init_app(app)
#
#         self.db = db
#         self.User = UserModel
#
#
#         @self.login_manager.user_loader
#         def load_user(user_id):
#             user =  self.User.query.get(user_id)
#             return user if user else AdminModel.query.get(user_id)
#
#
#     def generate_token(self, user_id):
#         """ Generate a JWT token with an expiration time. """
#         payload = {
#             "user_id": user_id,
#             "exp": NetworkDateTime.network_datetime() + timedelta(minutes=12)
#         }
#         return jwt.encode(payload=payload, key=self.SECRET_KEY)
#
#
#     def verify_token(self, token):
#         """ Decode and verify JWT token """
#         try:
#             payload = jwt.decode(token, self.SECRET_KEY, algorithms=["HS256"])
#             return payload['user_id']
#         except jwt.ExpiredSignatureError:
#             return None
#         except jwt.InvalidTokenError:
#             return None
#
#
#     def login(self, user: AdminModel | UserModel):
#         """Authenticate user and set token in cookies if successful"""
#         if user:
#             if user.email_verified is False:
#                 return jsonify({
#                     "code": 403,
#                     "status": "Account not verified"
#                 }), 403
#
#             token = self.generate_token(user.get_id())
#
#             date_time = NetworkDateTime.network_datetime().strftime('%a %d %b %Y, %I:%M%p')
#             date, time = date_time.split(', ')
#
#             login_info = login_device_info(request=request)
#             login_info['date'] = date
#             login_info['time'] = time
#
#             data = {
#                 'id': user.id,
#                 'first_name': user.first_name,
#                 'last_name': user.last_name,
#                 'email_address': user.email_address,
#                 'gender': user.gender,
#                 **login_info
#             }
#
#             response = make_response(jsonify({"message": "Login succesful", "data": data}), 200)
#             response.set_cookie("auth_token", token)
#             login_user(user=user)
#
#             context = data
#             login_template = render_template('login.html', **context)
#             login_data = {
#                 'recipient':user.email_address,
#                 'subject': 'Account Login',
#                 'template': login_template
#             }
#
#             # Mail sending should be handled as background task
#             # TODO: Integrete with Celery/Redis for task scheduling
#             emailHandler.sendMail(**login_data)
#
#             return response
#         return jsonify({"error": "Invalid credentials"}), 401
#
#
#     def logout(self):
#         """ Clear the authentication cookie to log the user out."""
#         response = make_response(jsonify({"message": "Logged out successfully"}))
#         response.set_cookie("auth_token", "", expires=0)
#         logout_user()
#         return response
#
#
#     def login_required(self, f):
#         """Decorator to protect routes needing authentication. """
#         @wraps(f)
#         def decorated(*args, **kwargs):
#             token = request.cookies.get('auth_token')
#             if not token:
#                 return jsonify({
#                     "code": 401,
#                     "error": "Token is missing",
#                     "message": "Login required"}), 401
#
#             user_id = self.verify_token(token)
#             if not user_id:
#                 return jsonify({
#                     "code": 401,
#                     "error": "Token is invalid or expired!",
#                     "message": "Re-authentication required"}), 401
#             kwargs['user_id'] = user_id
#             return f(*args, **kwargs)
#         return decorated
#
#
# auth = Auth()
