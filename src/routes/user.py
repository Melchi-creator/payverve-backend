"""
user.py

Defines all api routes for users resources especially CRUD
"""

from flask import Blueprint

from ..resources import UserResource

UserBlueprint = Blueprint("user", __name__)

UserBlueprint.route("/users", methods=['POST'])(UserResource.create)
UserBlueprint.route("/users", methods=['GET'])(UserResource.read_all)
UserBlueprint.route("/users/<uuid:id>", methods=['GET'])(UserResource.read_one)
UserBlueprint.route("/users/<uuid:id>", methods=['PUT'])(UserResource.update)
UserBlueprint.route("/users/<uuid:id>", methods=['DELETE'])(UserResource.delete)

UserBlueprint.route("/users/verify-email/<token>", methods=['GET'])(UserResource.verify_email)
UserBlueprint.route("/users/login", methods=['POST', 'GET'])(UserResource.login)
UserBlueprint.route("/users/logout", methods=['POST'])(UserResource.logout)

UserBlueprint.route("/users/request-password-reset", methods=['POST'])(UserResource.request_password_reset)
UserBlueprint.route("/users/reset-password/verify", methods=['GET'])(UserResource.verify_reset_token)
UserBlueprint.route("/users/reset-password", methods=['POST'])(UserResource.reset_password)
