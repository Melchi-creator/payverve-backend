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
                    'status_message': 'not found',
                    'message': 'user not found'
                }), 404

            if not new_user:
                if not customer_confirmation.email_verified or not customer_confirmation.account_active:
                    return jsonify({
                        'code': 403,
                        'status_message': 'forbidden',
                        'message': 'you are not allowed to create a kyc until your email is verified and account active'
                    }), 403

            if not created_by_payverve:
                return jsonify({
                    'code': 403,
                    'status_message': 'forbidden',
                    'message': 'you are not allowed to create a kyc'
                }), 403

            # noinspection PyArgumentList
            new_kyc = KYCModel(
                user_id=user_id,
            )
            new_kyc.save()

            return jsonify({
                'code': 201,
                'status_message': 'created',
                'message': 'kyc successfully created - tier 1'
            }), 201

        except IntegrityError:
            return jsonify({
                'code': 409,
                'status_message': 'conflict - integrity error',
                'message': 'this currency has already been listed'
            }), 409

        except DataError:
            return jsonify({
                'code': 400,
                'status_message': 'bad request - data error',
                'message': 'ensure input data are correct'
            }), 400

        except InternalError:
            return jsonify({
                'code': 500,
                'status_message': 'internal server - internal server error',
                'message': 'could not fetch data'
            }), 500

        except (OperationalError, DisconnectionError, SQLAlchemyError):
            return jsonify({
                'code': 500,
                'status_message': 'database error - operation, sqlalchemy and disconnection error',
                'message': 'could not fetch data'
            }), 500

        except ProgrammingError:
            return jsonify({
                'code': 500,
                'status_message': 'database error - programming error',
                'message': 'could not fetch table'
            }), 500

        except (ArithmeticError, ValueError, ZeroDivisionError):
            return jsonify({
                'code': 500,
                'status_message': 'calculation error - arithmetic, value, zerodivision error',
                'message': 'could run an arithmetic calculation'
            }), 500

    @staticmethod
    def read_all():
        """  """

        kycs = KYCModel.query.all()

        try:
            if not kycs:
                return jsonify({
                    'code': 404,
                    'status_message': 'data not found',
                    'message': 'no kycs was found'
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
                'status_message': 'success',
                'data': data
            }), 200

        except InternalError:
            return jsonify({
                'code': 500,
                'status_message': 'internal server - internal server error',
                'message': 'could not fetch data'
            }), 500

        except (OperationalError, DisconnectionError):
            return jsonify({
                'code': 500,
                'status_message': 'database error - operation and disconnection error',
                'message': 'could not fetch data'
            }), 500

        except ProgrammingError:
            return jsonify({
                'code': 500,
                'status_message': 'database error - programming error',
                'message': 'could not fetch table'
            }), 500

    @staticmethod
    def read_one(id=None):
        """  """

        kyc = KYCModel.query.filter_by(id=id).first()

        try:
            if not kyc:
                return jsonify({
                    'code': 404,
                    'status_message': 'data not found',
                    'message': 'no kyc was found'
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
                'status_message': 'success',
                'data': data
            }), 200

        except InternalError:
            return jsonify({
                'code': 500,
                'status_message': 'internal server - internal server error',
                'message': 'could not fetch data'
            }), 500

        except (OperationalError, DisconnectionError):
            return jsonify({
                'code': 500,
                'status_message': 'database error - operation and disconnection error',
                'message': 'could not fetch data'
            }), 500

        except ProgrammingError:
            return jsonify({
                'code': 500,
                'status_message': 'database error - programming error',
                'message': 'could not fetch table'
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
                    'status_message': 'data not found',
                    'message': 'the customer was not found'
                }), 404

            if 'bvn' in fields and fields['bvn'] is not None:
                if kyc.bvn_present:
                    return jsonify({
                        'code': 400,
                        'status_message': 'bad request',
                        'message': 'bvn has already been updated if you want to update it, contact support'
                    }), 400

                BVNCheck(fields['bvn'])

                kyc.bvn = fields['bvn']
                kyc.bvn_present = True
                kyc.tier = 2

            if 'nin' in fields and fields['nin'] is not None:
                if kyc.nin_present:
                    return jsonify({
                        'code': 400,
                        'status_message': 'bad request',
                        'message': 'nin has already been updated if you want to update it, contact support'
                    }), 400

                if not kyc.bvn_present and fields['bvn'] is None:
                    return jsonify({
                        'code': 400,
                        'status_message': 'bad request',
                        'message': 'provide bvn to update nin'
                    }), 400

                NINCheck(fields['nin'])

                kyc.nin = fields['nin']
                kyc.nin_present = True
                kyc.tier = 3

            kyc.save()

            return jsonify({
                'code': 200,
                'status_message': 'success',
                'message': "kyc successfully updated"
            }), 200

        except IntegrityError:
            return jsonify({
                'code': 409,
                'status_message': 'conflict',
                'message': 'bvn or nin has already been used, try another one'
            }), 409

        except InternalError:
            return jsonify({
                'code': 500,
                'status_message': 'internal server - internal server error',
                'message': 'could not fetch data'
            }), 500

        except (OperationalError, DisconnectionError):
            return jsonify({
                'code': 500,
                'status_message': 'database error - operation and disconnection error',
                'message': 'could not fetch data'
            }), 500

        except ProgrammingError:
            return jsonify({
                'code': 500,
                'status_message': 'database error - programming error',
                'message': 'could not fetch table'
            }), 500

        except ValueError as ve:
            return jsonify({
                'code': 400,
                'status_message': 'bad request - value error',
                'message': str(ve)
            }), 400
