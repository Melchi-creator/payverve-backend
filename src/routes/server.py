"""
server.py

Route for server check
"""

from flask import Blueprint

from ..resources import ServerResource

ServerBlueprint = Blueprint("server_check", __name__)

ServerBlueprint.route("/", methods=['GET'])(ServerResource.status_check)
