"""

"""

from flask import Blueprint

from ..auth import jwt_required
from ..resources import SpendSaveResource

SpendSaveBlueprint = Blueprint("spend_save", __name__)

SpendSaveBlueprint.route("/spend-saves", methods=['POST'])(jwt_required(SpendSaveResource.create))
SpendSaveBlueprint.route("/spend-saves", methods=['GET'])(jwt_required(SpendSaveResource.read_all))
SpendSaveBlueprint.route("/spend-saves/<uuid:id>", methods=['GET'])(jwt_required(SpendSaveResource.read_one))
SpendSaveBlueprint.route("/spend-saves/percentage-update/<uuid:id>", methods=['PUT'])(jwt_required(SpendSaveResource.update_percentage))
SpendSaveBlueprint.route("/spend-saves/toggle-spend-save/<uuid:id>", methods=['PUT'])(jwt_required(SpendSaveResource.toggle_spend_save))
SpendSaveBlueprint.route("/spend-saves/withdraw/<uuid:id>",
                         methods=['POST'])(jwt_required(SpendSaveResource.withdraw_spend_save))
SpendSaveBlueprint.route("/spend-saves/update-fund/<uuid:id>", methods=['PUT'])(jwt_required(SpendSaveResource.update_fund))
