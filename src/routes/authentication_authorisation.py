"""
src/routes/authentication_authorisation.py
This module defines the routes for user authentication and authorization.
It includes routes for admin and user login, utilizing the Authentication middleware.
"""

from flask import Blueprint

from ..middlewares import Authentication

LoginBlueprint = Blueprint("login", __name__)

LoginBlueprint.route("/admin-login", methods=['POST'])(Authentication.admin_authentication)
LoginBlueprint.route("/user-login", methods=['POST'])(Authentication.user_authentication)
LoginBlueprint.route("/user-refresh-token", methods=['POST'])(Authentication.refresh_token)
