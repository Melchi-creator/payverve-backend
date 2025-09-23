"""

"""
from flask import jsonify
from flask_restful import Resource
from flask_restful.reqparse import Argument
from sqlalchemy.exc import DisconnectionError, \
    InternalError, \
    OperationalError, \
    ProgrammingError

from ..models import KYCModel, VirtualAccountNumberModel
from ..utilities import parse_params
from ..value_object import BVNCheck, NINCheck


class VirtualAccountNumberResource(Resource):
    """  """

    @staticmethod
    def read_all():
        """  """

        virtual_account_numbers = VirtualAccountNumberModel.query.all()

        try:
            if not virtual_account_numbers:
                return jsonify({
                    'code': 404,
                    'code_status': 'data not found',
                    'message': 'no virtual accounts was found'
                }), 404

            data = [
                {
                    'id': virtual_account_number.id,
                    'response_code': virtual_account_number.response_code,
                    'response_message': virtual_account_number.response_message,
                    'flw_ref': virtual_account_number.flw_ref,
                    'order_ref': virtual_account_number.order_ref,
                    'frequency': virtual_account_number.frequency,
                    'created_at_by_flw': virtual_account_number.created_at_by_flw,
                    'expiry_date': virtual_account_number.expiry_date,
                    'account_number': virtual_account_number.account_number,
                    'bank_name': virtual_account_number.bank_name,
                    'note': virtual_account_number.note,
                    'amount': virtual_account_number.amount,
                    'currency_ticker': virtual_account_number.currency_ticker,
                    'is_active': virtual_account_number.is_active,
                    'user_id': virtual_account_number.user_id,
                    'currency_id': virtual_account_number.currency_id,
                    'created_at': virtual_account_number.created_at,
                    'updated_at': virtual_account_number.updated_at
                }
                for virtual_account_number in virtual_account_numbers
            ]

            return jsonify({
                'code': 200,
                'code_status': 'success',
                'data': data
            }), 200

        except InternalError:
            return jsonify({
                'code': 500,
                'code_status': 'internal server - internal server error',
                'message': 'could not fetch data'
            }), 500

        except (OperationalError, DisconnectionError):
            return jsonify({
                'code': 500,
                'code_status': 'database error - operation and disconnection error',
                'message': 'could not fetch data'
            }), 500

        except ProgrammingError:
            return jsonify({
                'code': 500,
                'code_status': 'database error - programming error',
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
                    'code_status': 'data not found',
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
                'code_status': 'success',
                'data': data
            }), 200

        except InternalError:
            return jsonify({
                'code': 500,
                'code_status': 'internal server - internal server error',
                'message': 'could not fetch data'
            }), 500

        except (OperationalError, DisconnectionError):
            return jsonify({
                'code': 500,
                'code_status': 'database error - operation and disconnection error',
                'message': 'could not fetch data'
            }), 500

        except ProgrammingError:
            return jsonify({
                'code': 500,
                'code_status': 'database error - programming error',
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
                    'code_status': 'data not found',
                    'message': 'the customer was not found'
                }), 404

            if 'bvn' in fields and fields['bvn'] is not None:
                if kyc.bvn_present:
                    return jsonify({
                        'code': 400,
                        'code_status': 'bad request',
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
                        'code_status': 'bad request',
                        'message': 'nin has already been updated if you want to update it, contact support'
                    }), 400

                if not kyc.bvn_present and fields['bvn'] is None:
                    return jsonify({
                        'code': 400,
                        'code_status': 'bad request',
                        'message': 'provide bvn to update nin'
                    }), 400

                NINCheck(fields['nin'])

                kyc.nin = fields['nin']
                kyc.nin_present = True
                kyc.tier = 3

            kyc.save()

            return jsonify({
                'code': 200,
                'code_status': 'success',
                'data': "kyc successfully updated"
            }), 200

        except InternalError:
            return jsonify({
                'code': 500,
                'code_status': 'internal server - internal server error',
                'message': 'could not fetch data'
            }), 500

        except (OperationalError, DisconnectionError):
            return jsonify({
                'code': 500,
                'code_status': 'database error - operation and disconnection error',
                'message': 'could not fetch data'
            }), 500

        except ProgrammingError:
            return jsonify({
                'code': 500,
                'code_status': 'database error - programming error',
                'message': 'could not fetch table'
            }), 500

        except ValueError as ve:
            return jsonify({
                'code': 400,
                'code_status': 'bad request - value error',
                'message': str(ve)
            }), 400
