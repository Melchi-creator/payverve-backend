"""
authentication_authorisation.py

Defines all api routes for authentication and authorisation resources
"""

from flask import Blueprint

from ..resources import AuthResource

LoginBlueprint = Blueprint("login", __name__)

LoginBlueprint.route("/admin-login", methods=['POST'])(AuthResource.admin_login)
LoginBlueprint.route("/user-login", methods=['POST'])(AuthResource.user_login)
