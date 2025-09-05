"""

"""
from flask import jsonify, request
from flask_restful import Resource
from sqlalchemy.exc import DataError, \
    DisconnectionError, \
    IntegrityError, \
    InternalError, \
    OperationalError, \
    ProgrammingError, \
    SQLAlchemyError

from ..models import KYCModel, UserModel


class KYCResource(Resource):
    """  """

    @staticmethod
    def create():
        """  """

        try:

            user_id = request.json.get('user_id')
            email_address = request.json.get('email_address')
            created_by_payverve = request.json.get('created_by_payverve')

            customer_confirmation = UserModel.query.filter_by(id=user_id, email_address=email_address).first()

            if not customer_confirmation:
                return jsonify({
                    'code': 404,
                    'code_status': 'not found',
                    'data': 'user not found'
                }), 404

            if not created_by_payverve:
                return jsonify({
                    'code': 403,
                    'code_status': 'forbidden',
                    'message': 'you are not allowed to create a kyc'
                }), 403

            # noinspection PyArgumentList
            new_kyc = KYCModel(
                user_id=user_id,
            )
            new_kyc.save()

            return jsonify({
                'code': 201,
                'code_status': 'created',
                'data': 'kyc successfully created - tier 1'
            }), 201

        except IntegrityError:
            return jsonify({
                'code': 409,
                'code_status': 'conflict - integrity error',
                'message': 'this currency has already been listed'
            }), 409

        except DataError:
            return jsonify({
                'code': 400,
                'code_status': 'bad request - data error',
                'message': 'ensure input data are correct'
            }), 400

        except InternalError:
            return jsonify({
                'code': 500,
                'code_status': 'internal server - internal server error',
                'data': 'could not fetch data'
            }), 500

        except (OperationalError, DisconnectionError, SQLAlchemyError):
            return jsonify({
                'code': 500,
                'code_status': 'database error - operation, sqlalchemy and disconnection error',
                'data': 'could not fetch data'
            }), 500

        except ProgrammingError:
            return jsonify({
                'code': 500,
                'code_status': 'database error - programming error',
                'data': 'could not fetch table'
            }), 500

        except (ArithmeticError, ValueError, ZeroDivisionError):
            return jsonify({
                'code': 500,
                'code_status': 'calculation error - arithmetic, value, zerodivision error',
                'data': 'could run an arithmetic calculation'
            }), 500

    @staticmethod
    def read_all():
        """  """

        kycs = KYCModel.query.all()

        try:
            if not kycs:
                return jsonify({
                    'code': 404,
                    'code_status': 'data not found',
                    'data': 'no kycs was found'
                }), 404

            data = []

            for kyc in kycs:
                data.append({
                    'id': kyc.id,
                    'tier': kyc.tier,
                    'bvn': kyc.bvn,
                    'referred_id': kyc.referred_id,
                    'bvn_present': kyc.bvn_present,
                    'nin_present': kyc.nin_present,
                    'user_id': kyc.user_id,
                    'created_at': kyc.created_at,
                    'updated_at': kyc.updated_at
                })

            return jsonify({
                'code': 200,
                'code_status': 'success',
                'data': data
            }), 200

        except InternalError:
            return jsonify({
                'code': 500,
                'code_status': 'internal server - internal server error',
                'data': 'could not fetch data'
            }), 500

        except (OperationalError, DisconnectionError):
            return jsonify({
                'code': 500,
                'code_status': 'database error - operation and disconnection error',
                'data': 'could not fetch data'
            }), 500

        except ProgrammingError:
            return jsonify({
                'code': 500,
                'code_status': 'database error - programming error',
                'data': 'could not fetch table'
            }), 500

    @staticmethod
    def read_one(id=None):
        """  """

        kyc = KYCModel.query.filter_by(id=id).first()

        try:
            if not kyc:
                return jsonify({
                    'code': 404,
                    'code_status': 'data not found',
                    'data': 'no kyc was found'
                }), 404

            data = {
                'id': kyc.id,
                'tier': kyc.tier,
                'bvn': kyc.bvn,
                'nin': kyc.nin,
                'bvn_present': kyc.bvn_present,
                'nin_present': kyc.nin_present,
                'user_id': kyc.user_id,
                'created_at': kyc.created_at,
                'updated_at': kyc.updated_at
            }

            return jsonify({
                'code': 200,
                'code_status': 'success',
                'data': data
            }), 200

        except InternalError:
            return jsonify({
                'code': 500,
                'code_status': 'internal server - internal server error',
                'data': 'could not fetch data'
            }), 500

        except (OperationalError, DisconnectionError):
            return jsonify({
                'code': 500,
                'code_status': 'database error - operation and disconnection error',
                'data': 'could not fetch data'
            }), 500

        except ProgrammingError:
            return jsonify({
                'code': 500,
                'code_status': 'database error - programming error',
                'data': 'could not fetch table'
            }), 500
