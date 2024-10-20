"""
server.py
This file is for the route that verifies the server is running and accessbile
"""
from flask import Blueprint

from src.resources import Server

ServerBlueprint = Blueprint("server", __name__)

ServerBlueprint.route("/", methods=['GET'])(Server.server)
