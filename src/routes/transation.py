"""

"""

from flask import Blueprint

from ..auth import jwt_required
from ..resources.transaction import TransactionResource

TransactionBlueprint = Blueprint("transation", __name__)

TransactionBlueprint.route("/transactions", methods=['GET'])(jwt_required(TransactionResource.read_all))
TransactionBlueprint.route("/transactions/<uuid:id>", methods=['GET'])(jwt_required(TransactionResource.read_one))
TransactionBlueprint.route("/transactions/user/<uuid:id>",
                           methods=['GET'])(jwt_required(TransactionResource.user_transation))
