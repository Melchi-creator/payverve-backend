"""

"""

from flask import Blueprint

from ..resources import ReferralResource

ReferralBlueprint = Blueprint("referral", __name__)

ReferralBlueprint.route("/referrals", methods=['POST'])(ReferralResource.create)
ReferralBlueprint.route("/referrals", methods=['GET'])(ReferralResource.read_all)
ReferralBlueprint.route("/referrals/<uuid:id>", methods=['GET'])(ReferralResource.read_one)
