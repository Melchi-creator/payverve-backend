"""
admin_roles.py

Defines all api routes for admin-roles resources especially CRUD
"""

from flask import Blueprint

from ..auth import admin_required, jwt_required
from ..resources import AdminRoleResource

AdminRoleBlueprint = Blueprint("admin_role", __name__)

AdminRoleBlueprint.route("/admin-roles", methods=['POST'])(jwt_required(admin_required(AdminRoleResource.create)))
AdminRoleBlueprint.route("/admin-roles", methods=['GET'])(jwt_required(admin_required(AdminRoleResource.read_all)))
AdminRoleBlueprint.route("/admin-roles/<uuid:id>", methods=['GET'])(jwt_required(admin_required(AdminRoleResource.read_one)))
AdminRoleBlueprint.route("/admin-roles/<uuid:id>", methods=['PUT'])(jwt_required(admin_required(AdminRoleResource.update)))
AdminRoleBlueprint.route("/admin-roles/<uuid:id>", methods=['DELETE'])(jwt_required(admin_required(AdminRoleResource.delete)))
