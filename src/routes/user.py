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
UserBlueprint.route("/users/login", methods=['POST'])(UserResource.login)
UserBlueprint.route("/users/logout", methods=['POST'])(UserResource.logout)
