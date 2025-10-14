"""

"""
from flask import jsonify, request
from flask_restful import Resource
from flask_restful.reqparse import Argument
from sqlalchemy.exc import DataError, \
    DisconnectionError, \
    IntegrityError, \
    InternalError, \
    OperationalError, \
    ProgrammingError, \
    SQLAlchemyError

from ..models import KYCModel, UserModel
from ..utilities import parse_params
from ..value_object import BVNCheck, NINCheck


class KYCResource(Resource):
    """  """

    @staticmethod
    def create():
        """  """

        try:

            user_id = request.json.get('user_id')
            email_address = request.json.get('email_address')
            created_by_payverve = request.json.get('created_by_payverve')
            new_user = request.json.get('new_user')

            customer_confirmation = UserModel.query.filter_by(id=user_id, email_address=email_address).first()

            if not customer_confirmation:
                return jsonify({
                    'code': 404,
                    'message': 'not found',
                    'data': 'user not found'
                }), 404

            if not new_user:
                if not customer_confirmation.email_verified or not customer_confirmation.account_active:
                    return jsonify({
                        'code': 403,
                        'message': 'forbidden',
                        'data': 'you are not allowed to create a kyc until your email is verified and account active'
                    }), 403

            if not created_by_payverve:
                return jsonify({
                    'code': 403,
                    'message': 'forbidden',
                    'data': 'you are not allowed to create a kyc'
                }), 403

            # noinspection PyArgumentList
            new_kyc = KYCModel(
                user_id=user_id,
            )
            new_kyc.save()

            return jsonify({
                'code': 201,
                'message': 'created',
                'data': 'kyc successfully created - tier 1'
            }), 201

        except IntegrityError:
            return jsonify({
                'code': 409,
                'message': 'conflict - integrity error',
                'data': 'this currency has already been listed'
            }), 409

        except DataError:
            return jsonify({
                'code': 400,
                'message': 'bad request - data error',
                'data': 'ensure input data are correct'
            }), 400

        except InternalError:
            return jsonify({
                'code': 500,
                'message': 'internal server - internal server error',
                'data': 'could not fetch data'
            }), 500

        except (OperationalError, DisconnectionError, SQLAlchemyError):
            return jsonify({
                'code': 500,
                'message': 'database error - operation, sqlalchemy and disconnection error',
                'data': 'could not fetch data'
            }), 500

        except ProgrammingError:
            return jsonify({
                'code': 500,
                'message': 'database error - programming error',
                'data': 'could not fetch table'
            }), 500

        except (ArithmeticError, ValueError, ZeroDivisionError):
            return jsonify({
                'code': 500,
                'message': 'calculation error - arithmetic, value, zerodivision error',
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
                    'message': 'data not found',
                    'data': 'no kycs was found'
                }), 404

            data = []

            for kyc in kycs:
                data.append({
                    'id': kyc.id,
                    'tier': kyc.tier,
                    'bvn': kyc.bvn,
                    'nin': kyc.nin,
                    'bvn_present': kyc.bvn_present,
                    'nin_present': kyc.nin_present,
                    'user_id': kyc.user_id,
                    'created_at': kyc.created_at,
                    'updated_at': kyc.updated_at
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
        """  """

        kyc = KYCModel.query.filter_by(id=id).first()

        try:
            if not kyc:
                return jsonify({
                    'code': 404,
                    'message': 'data not found',
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
        Argument("bvn", location="json"),
        Argument("nin", location="json"),
    )
    def update(id=None, **fields):
        """  """

        kyc = KYCModel.query.filter_by(user_id=id).first()

        # @TODO: use dojah for nin and bvn verification

        try:
            if not kyc:
                return jsonify({
                    'code': 404,
                    'message': 'data not found',
                    'data': 'the customer was not found'
                }), 404

            if 'bvn' in fields and fields['bvn'] is not None:
                if kyc.bvn_present:
                    return jsonify({
                        'code': 400,
                        'message': 'bad request',
                        'data': 'bvn has already been updated if you want to update it, contact support'
                    }), 400

                BVNCheck(fields['bvn'])

                kyc.bvn = fields['bvn']
                kyc.bvn_present = True
                kyc.tier = 2

            if 'nin' in fields and fields['nin'] is not None:
                if kyc.nin_present:
                    return jsonify({
                        'code': 400,
                        'message': 'bad request',
                        'data': 'nin has already been updated if you want to update it, contact support'
                    }), 400

                if not kyc.bvn_present and fields['bvn'] is None:
                    return jsonify({
                        'code': 400,
                        'message': 'bad request',
                        'data': 'provide bvn to update nin'
                    }), 400

                NINCheck(fields['nin'])

                kyc.nin = fields['nin']
                kyc.nin_present = True
                kyc.tier = 3

            kyc.save()

            return jsonify({
                'code': 200,
                'message': 'success',
                'data': "kyc successfully updated"
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

        except ValueError as ve:
            return jsonify({
                'code': 400,
                'message': 'bad request - value error',
                'data': str(ve)
            }), 400
