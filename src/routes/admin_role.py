"""
admin_roles.py

Defines all api routes for admin-roles resources especially CRUD
"""

from flask import Blueprint

from ..resources import AdminRoleResource

AdminRoleBlueprint = Blueprint("admin_role", __name__)

AdminRoleBlueprint.route("/admin-roles", methods=['POST'])(AdminRoleResource.create)
AdminRoleBlueprint.route("/admin-roles", methods=['GET'])(AdminRoleResource.read_all)
AdminRoleBlueprint.route("/admin-roles/<uuid:id>", methods=['GET'])(AdminRoleResource.read_one)
AdminRoleBlueprint.route("/admin-roles/<uuid:id>", methods=['PUT'])(AdminRoleResource.update)
AdminRoleBlueprint.route("/admin-roles/<uuid:id>", methods=['DELETE'])(AdminRoleResource.delete)
