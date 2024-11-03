"""
admin_roles.py

Defines all api routes for admin-roles resources especially CRUD
"""

from flask import Blueprint

from ..resources import AdminRolesResource

AdminRoleBlueprint = Blueprint("admin_role", __name__)

AdminRoleBlueprint.route("/admin-roles", methods=['POST'])(AdminRolesResource.create)
AdminRoleBlueprint.route("/admin-roles", methods=['GET'])(AdminRolesResource.read_all)
AdminRoleBlueprint.route("/admin-roles/<uuid:id>", methods=['GET'])(AdminRolesResource.read_one)
AdminRoleBlueprint.route("/admin-roles/<uuid:id>", methods=['PUT'])(AdminRolesResource.update)
AdminRoleBlueprint.route("/admin-roles/<uuid:id>", methods=['DELETE'])(AdminRolesResource.delete)
