"""
admin.py

Defines all api routes for admin resources especially CRUD
"""

from flask import Blueprint

from ..resources import AdminResource

AdminBlueprint = Blueprint("admin", __name__)

AdminBlueprint.route("/admins", methods=['POST'])(AdminResource.create)
AdminBlueprint.route("/admins", methods=['GET'])(AdminResource.read_all)
AdminBlueprint.route("/admins/<uuid:id>", methods=['GET'])(AdminResource.read_one)
AdminBlueprint.route("/admins/<uuid:id>", methods=['PUT'])(AdminResource.update)
AdminBlueprint.route("/admins/<uuid:id>", methods=['DELETE'])(AdminResource.delete)
