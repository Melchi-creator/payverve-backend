"""
beneficiary.py

Defines all api routes for beneficiaries resources especially CRUD
"""

from flask import Blueprint

from ..resources import BeneficiaryResource

BeneficiaryBlueprint = Blueprint("beneficiary", __name__)

BeneficiaryBlueprint.route("/beneficiaries", methods=['POST'])(BeneficiaryResource.create)
BeneficiaryBlueprint.route("/beneficiaries", methods=['GET'])(BeneficiaryResource.read_all)
BeneficiaryBlueprint.route("/beneficiaries/<uuid:id>", methods=['GET'])(BeneficiaryResource.read_one)
BeneficiaryBlueprint.route("/beneficiaries/<uuid:id>", methods=['PUT'])(BeneficiaryResource.update)
BeneficiaryBlueprint.route("/beneficiaries/<uuid:id>", methods=['DELETE'])(BeneficiaryResource.delete)