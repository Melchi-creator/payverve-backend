"""
beneficiary.py

Defines all functions for beneficiaries especially CRUD
"""
from flask import jsonify
from flask_restful import Resource
from flask_restful.reqparse import Argument
from sqlalchemy.exc import (DataError, DisconnectionError, IntegrityError,
                            InternalError, OperationalError, ProgrammingError,
                            SQLAlchemyError)

from ..models import BeneficiaryModel, UserModel
from ..utilities import parse_params


class BeneficiaryResource(Resource):
    """Class definition for Beneficiary Resources """

    @staticmethod
    @parse_params(
        Argument("user", location="json", required=True),
        Argument("name", location="json", required=True),
        Argument("account_number", location="json", required=True),
        Argument("bank", location="json", required=True),
        Argument("country", location="json", required=True),
    )
    def create(user, name, account_number, bank, country):
        """ Adds new beneficiary to User """

        _user = UserModel.query.filter_by(id=user).first()
        _beneficiary = BeneficiaryModel.query.filter_by(user=user, account_number=account_number).first()

        try:
            if not _user:
                return jsonify({
                    'code': 404,
                    'message': 'data not found',
                    'data': 'no user account was found'
                }), 404

            if _beneficiary:
                return jsonify({
                    'code': 409,
                    'message': 'conflict',
                    'data': 'You already have this account as a beneficiary'
                }), 409

            # noinspection PyArgumentList
            new_beneficiary = BeneficiaryModel(
                name=name,
                account_number=account_number,
                bank=bank,
                country=country,
                user=_user.id
            )
            new_beneficiary.save()

            data = {
                "id": new_beneficiary.id,
                "user": new_beneficiary.user,
                "name": new_beneficiary.name,
                "account_number": new_beneficiary.account_number,
                "bank": new_beneficiary.bank,
                "country": new_beneficiary.country
            }

            return jsonify({
                'code': 201,
                'message': 'created',
                # 'data': 'beneficiary was succefully added',
                'data': data  # 'data': 'beneficiary was succefully added',

            }), 201

        except DataError:
            return jsonify({
                'code': 400,
                'message': 'bad request - data error',
                'data': 'ensure input data are correct'
            }), 400

        except IntegrityError:
            return jsonify({
                'code': 409,
                'message': 'conflict - integrity error',
                'data': 'this beneficiary has already been listed'
            }), 409

        except InternalError:
            return jsonify({
                'code': 500,
                'message': 'Internal server - internal server error',
                'data': 'could not fetch data'
            }), 500

        except ProgrammingError:
            return jsonify({
                'code': 500,
                'message': 'databaser error - programming error',
                'data': 'could not fetch table'
            }), 500

        except (OperationalError, DisconnectionError, SQLAlchemyError):
            return jsonify({
                'code': 500,
                'message': 'database error - operation, sqlalchemy and disconnection error',
                'data': 'could not reach data'
            }), 500

    @staticmethod
    def read_all():
        """ Retrieves all beneficiaries """

        __beneficiaries = BeneficiaryModel.query.all()

        data = []

        try:
            if not __beneficiaries:
                return jsonify({
                    'code': 404,
                    'message': 'data not found',
                    'data': 'no beneficiary was found'
                }), 404

            for beneficiary in __beneficiaries:
                data.append({
                    "id": beneficiary.id,
                    "user": beneficiary.user,
                    "name": beneficiary.name,
                    "account_number": beneficiary.account_number,
                    "bank": beneficiary.bank,
                    "country": beneficiary.country
                })
            return jsonify({
                'code': 200,
                'message': 'success',
                'data': data
            }), 200

        except InternalError:
            return jsonify({
                'code': 500,
                'message': 'internal server - internal server error',
                'data': 'could not fetch data'
            }), 500

        except (OperationalError, DisconnectionError):
            return jsonify({
                'code': 500,
                'message': 'database error - operation and disconnection error',
                'data': 'could not fetch data'
            }), 500

        except ProgrammingError:
            return jsonify({
                'code': 500,
                'message': 'database error - programming error',
                'data': 'could not fetch table'
            }), 500

    @staticmethod
    def read_one(id=None):
        """ Retrieves a beneficiary by id """

        beneficiary = BeneficiaryModel.query.filter_by(id=id).first()

        try:
            if not beneficiary:
                return jsonify({
                    'code': 404,
                    'message': 'data not found',
                    'data': 'no beneficiary was found'
                }), 404

            data = {
                "id": beneficiary.id,
                "user": beneficiary.user,
                "name": beneficiary.name,
                "account_number": beneficiary.account_number,
                "bank": beneficiary.bank,
                "country": beneficiary.country
            }

            return jsonify({
                'code': 200,
                'message': 'success',
                'data': data
            }), 200

        except InternalError:
            return jsonify({
                'code': 500,
                'message': 'internal server - internal server error',
                'data': 'could not fetch data'
            }), 500

        except (OperationalError, DisconnectionError):
            return jsonify({
                'code': 500,
                'message': 'database error - operation and disconnection error',
                'data': 'could not fetch data'
            }), 500

        except ProgrammingError:
            return jsonify({
                'code': 500,
                'message': 'database error - programming error',
                'data': 'could not fetch table'
            }), 500

    @staticmethod
    @parse_params(
        Argument("name", location="json"),
        Argument("account_number", location="json"),
        Argument("bank", location="json"),
        Argument("country", location="json"),
    )
    def update(id=None, **fields):
        """ Updates a beneficiary by id """

        beneficiary = BeneficiaryModel.query.filter_by(id=id).first()

        try:
            if not beneficiary:
                return jsonify({
                    'code': 404,
                    'message': 'data not found',
                    'data': 'no benficiary was found'
                }), 404

            for key, value in fields.items():
                if value:
                    setattr(beneficiary, key, value)

            beneficiary.save()

            data = {
                "id": beneficiary.id,
                "user": beneficiary.user,
                "name": beneficiary.name,
                "account_number": beneficiary.account_number,
                "bank": beneficiary.bank,
                "country": beneficiary.country
            }

            return jsonify({
                'code': 200,
                'message': 'success',
                'data': data
            }), 200


        except InternalError:
            return jsonify({
                'code': 500,
                'message': 'internal server - internal server error',
                'data': 'could not fetch data'
            }), 500

        except (OperationalError, DisconnectionError):
            return jsonify({
                'code': 500,
                'message': 'database error - operation and disconnection error',
                'data': 'could not fetch data'
            }), 500

        except ProgrammingError:
            return jsonify({
                'code': 500,
                'message': 'database error - programming error',
                'data': 'could not fetch table'
            }), 500

    @staticmethod
    def delete(id=None):
        """ Updates a beneficiary by id """

        beneficiay = BeneficiaryModel.query.filter_by(id=id).first()

        try:
            if not beneficiay:
                return jsonify({
                    'code': 404,
                    'message': 'data not found',
                    'data': 'no beneficiary was found'
                }), 404

            beneficiay.delete()

            return jsonify({
                'code': 200,
                'message': 'success',
                'data': 'beneficiary was deleted successfully'
            }), 200

        except InternalError:
            return jsonify({
                'code': 500,
                'message': 'internal server - internal server error',
                'data': 'could not fetch data'
            }), 500

        except (OperationalError, DisconnectionError):
            return jsonify({
                'code': 500,
                'message': 'database error - operation and disconnection error',
                'data': 'could not fetch data'
            }), 500

        except ProgrammingError:
            return jsonify({
                'code': 500,
                'message': 'database error - programming error',
                'data': 'could not fetch table'
            }), 500
