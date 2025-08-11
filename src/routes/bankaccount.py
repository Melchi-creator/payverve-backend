"""
bank account.py

Defines all api routes for the bank account resources especially CRUD
"""

from flask import Blueprint

from ..resources import BankAccountResource

BeneficiaryBlueprint = Blueprint("bankaccount", __name__)

BeneficiaryBlueprint.route("/account", methods=['POST'])(BankAccountResource.create)
BeneficiaryBlueprint.route("/account", methods=['GET'])(BankAccountResource.read_all)
BeneficiaryBlueprint.route("/account/<uuid:id>", methods=['GET'])(BankAccountResource.read_one)
BeneficiaryBlueprint.route("/account/<uuid:id>", methods=['PUT'])(BankAccountResource.update)
BeneficiaryBlueprint.route("/account/<uuid:id>", methods=['DELETE'])(BankAccountResource.delete)
