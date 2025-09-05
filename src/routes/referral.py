"""

"""

from flask import Blueprint

from ..auth import jwt_required
from ..resources import ReferralResource

ReferralBlueprint = Blueprint("referral", __name__)

ReferralBlueprint.route("/referrals", methods=['POST'])(ReferralResource.create)
ReferralBlueprint.route("/referrals", methods=['GET'])(jwt_required(ReferralResource.read_all))
ReferralBlueprint.route("/referrals/<uuid:id>", methods=['GET'])(jwt_required(ReferralResource.read_one))
