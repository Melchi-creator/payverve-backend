"""
src/routes/user.py
This module defines the UserBlueprint for user-related routes in the Flask application.
It includes routes for creating, reading, updating, and deleting users.
"""

from flask import Blueprint

from ..middlewares import jwt_required
from ..resources import UserResource

UserBlueprint = Blueprint("user", __name__)

UserBlueprint.route("/users", methods=['POST'])(UserResource.create)
UserBlueprint.route("/users/verify", methods=['POST'])(UserResource.email_otp_base_verification)
UserBlueprint.route("/users/resend-email", methods=['POST'])(UserResource.resend_email_otp_base_verification)
UserBlueprint.route("/users", methods=['GET'])(jwt_required(UserResource.read_all))
UserBlueprint.route("/users/<uuid:id>", methods=['GET'])(jwt_required(UserResource.read_one))
UserBlueprint.route("/users/<uuid:id>", methods=['PUT'])(jwt_required(UserResource.update))
UserBlueprint.route("/users/<uuid:id>", methods=['DELETE'])(jwt_required(UserResource.delete))

# UserBlueprint.route("/users/verify-email/<token>", methods=['GET'])(UserResource.verify_email)
# UserBlueprint.route("/users/login", methods=['POST', 'GET'])(UserResource.login)
# UserBlueprint.route("/users/logout", methods=['POST'])(UserResource.logout)
#
# UserBlueprint.route("/users/request-password-reset", methods=['POST'])(UserResource.request_password_reset)
# UserBlueprint.route("/users/reset-password/verify", methods=['GET'])(UserResource.verify_reset_token)
# UserBlueprint.route("/users/reset-password", methods=['POST'])(UserResource.reset_password)
