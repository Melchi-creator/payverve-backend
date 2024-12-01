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

# AdminBlueprint.route("/admins/login", methods=['POST'])(AdminResource.login)
# AdminBlueprint.route("/admins/logout", methods=['POST'])(AdminResource.logout)
# AdminBlueprint.route("/admins/verify-email/<token>", methods=['GET'])(AdminResource.verify_email)
#
# AdminBlueprint.route("/admins/request-password-reset", methods=['POST'])(AdminResource.request_password_reset)
# AdminBlueprint.route("/admins/reset-password/verify", methods=['GET'])(AdminResource.verify_reset_token)
# AdminBlueprint.route("/admins/reset-password", methods=['POST'])(AdminResource.reset_password)
