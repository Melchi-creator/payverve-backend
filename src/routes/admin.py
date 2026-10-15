"""
admin.py

Defines all api routes for admin resources especially CRUD
"""

from flask import Blueprint

from ..auth import admin_required, jwt_required
from ..resources import AdminResource

# Every one of these was unauthenticated. With no admin rows in the
# database, POST /admin-roles followed by POST /admins let anyone mint
# the first admin account and inherit platform-wide read access.
AdminBlueprint = Blueprint("admin", __name__)

AdminBlueprint.route("/admins", methods=['POST'])(jwt_required(admin_required(AdminResource.create)))
AdminBlueprint.route("/admins", methods=['GET'])(jwt_required(admin_required(AdminResource.read_all)))
AdminBlueprint.route("/admins/<uuid:id>", methods=['GET'])(jwt_required(admin_required(AdminResource.read_one)))
AdminBlueprint.route("/admins/<uuid:id>", methods=['PUT'])(jwt_required(admin_required(AdminResource.update)))
AdminBlueprint.route("/admins/<uuid:id>", methods=['DELETE'])(jwt_required(admin_required(AdminResource.delete)))

# AdminBlueprint.route("/admins/login", methods=['POST'])(AdminResource.login)
# AdminBlueprint.route("/admins/logout", methods=['POST'])(AdminResource.logout)
# AdminBlueprint.route("/admins/verify-email/<token>", methods=['GET'])(AdminResource.verify_email)
#
# AdminBlueprint.route("/admins/request-password-reset", methods=['POST'])(AdminResource.request_password_reset)
# AdminBlueprint.route("/admins/reset-password/verify", methods=['GET'])(AdminResource.verify_reset_token)
# AdminBlueprint.route("/admins/reset-password", methods=['POST'])(AdminResource.reset_password)
