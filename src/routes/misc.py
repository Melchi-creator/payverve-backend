"""

"""

from flask import Blueprint

from ..auth import jwt_required
from ..resources import MiscellaneousResources

MiscellaneousBlueprint = Blueprint("list_bank", __name__)

MiscellaneousBlueprint.route("/list-banks", methods=['GET'])(jwt_required(MiscellaneousResources.list_ngn_banks))
MiscellaneousBlueprint.route("/list-bell-banks", methods=['GET'])(jwt_required(MiscellaneousResources.list_bell_ngn_banks))
