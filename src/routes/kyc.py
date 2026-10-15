"""

"""

from flask import Blueprint

from ..auth import jwt_required
from ..resources import KYCResource

KYCBlueprint = Blueprint("kyc", __name__)

# Unauthenticated, and vestigial: registration stages the KYC row itself.
# The app only ever uses PUT /kycs/<id>.
KYCBlueprint.route("/kycs", methods=['POST'])(
    jwt_required(KYCResource.create))
KYCBlueprint.route("/kycs", methods=['GET'])(jwt_required(KYCResource.read_all))
KYCBlueprint.route("/kycs/<uuid:id>", methods=['GET'])(jwt_required(KYCResource.read_one))
KYCBlueprint.route("/kycs/<uuid:id>", methods=['PUT'])(jwt_required(KYCResource.update))