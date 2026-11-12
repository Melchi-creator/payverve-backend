"""
beneficiary.py

Defines all api routes for beneficiaries resources especially CRUD
"""

from flask import Blueprint

from ..auth import jwt_required
from ..resources import BeneficiaryResource

# These were all unauthenticated, and read_all returned every saved
# payee on the platform -- names, banks and account numbers.
BeneficiaryBlueprint = Blueprint("beneficiary", __name__)

BeneficiaryBlueprint.route("/beneficiaries", methods=['POST'])(jwt_required(BeneficiaryResource.create))
BeneficiaryBlueprint.route("/beneficiaries", methods=['GET'])(jwt_required(BeneficiaryResource.read_all))
BeneficiaryBlueprint.route("/beneficiaries/<uuid:id>", methods=['GET'])(jwt_required(BeneficiaryResource.read_one))
BeneficiaryBlueprint.route("/beneficiaries/<uuid:id>", methods=['PUT'])(jwt_required(BeneficiaryResource.update))
BeneficiaryBlueprint.route("/beneficiaries/<uuid:id>", methods=['DELETE'])(jwt_required(BeneficiaryResource.delete))
