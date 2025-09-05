"""

"""

from flask import Blueprint

from ..auth import jwt_required
from ..resources import KYCResource

KYCBlueprint = Blueprint("kyc", __name__)

KYCBlueprint.route("/kycs", methods=['POST'])(KYCResource.create)
KYCBlueprint.route("/kycs", methods=['GET'])(jwt_required(KYCResource.read_all))
KYCBlueprint.route("/kycs/<uuid:id>", methods=['GET'])(jwt_required(KYCResource.read_one))
KYCBlueprint.route("/kycs/<uuid:id>", methods=['PUT'])(jwt_required(KYCResource.update))