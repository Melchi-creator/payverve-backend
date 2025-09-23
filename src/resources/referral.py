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

from ..models import CurrencyModel, ReferralModel, UserModel, WalletModel
from ..utilities import Cryptographer
from ..value_object import MinimumBalance


class ReferralResource(Resource):
    """  """

    @staticmethod
    def create():
        """  """

        try:

            referral_id = request.json.get('referral_id')
            referral_code = request.json.get('referral_code')
            referred_id = request.json.get('referred_id')
            referred_code = request.json.get('referred_code')
            email_address = request.json.get('email_address')
            created_by_payverve = request.json.get('created_by_payverve')

            customer_confirmation = UserModel.query.filter_by(id=referred_id, email_address=email_address).first()

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
                    'message': 'you are not allowed to create a referral'
                }), 403

            # noinspection PyArgumentList
            new_referred = ReferralModel(
                referral_id=referral_id,
                referral_code=referral_code,
                referred_id=referred_id,
                referred_code=referred_code
            )
            new_referred.save()

            ngn_wallet = CurrencyModel.query.filter_by(short_code='ngn').first().id

            referral_wallet = WalletModel.query.filter_by(user_id=referral_id, currency_id=ngn_wallet).first()
            referred_wallet = WalletModel.query.filter_by(user_id=referred_id, currency_id=ngn_wallet).first()

            decrypted_referral_fund = Cryptographer.decrypt(referral_wallet.fund)
            decrypted_referred_fund = Cryptographer.decrypt(referred_wallet.fund)

            current_decrypted_referral_fund = float(decrypted_referral_fund)
            current_decrypted_referred_fund = float(decrypted_referred_fund)

            MinimumBalance(current_decrypted_referral_fund)
            MinimumBalance(current_decrypted_referred_fund)

            bonus_fund = float(500.00)

            referral_bonus = bonus_fund + current_decrypted_referral_fund
            referred_bonus = bonus_fund + current_decrypted_referred_fund

            encrypt_referral_fund = Cryptographer.encrypt(referral_bonus)
            encrypt_referred_fund = Cryptographer.encrypt(referred_bonus)

            referral_wallet.fund = encrypt_referral_fund
            referral_wallet.save()

            referred_wallet.fund = encrypt_referred_fund
            referred_wallet.save()

            return jsonify({
                'code': 201,
                'code_status': 'created',
                'data': 'referral successfully registered'
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

        referrals = ReferralModel.query.all()

        try:
            if not referrals:
                return jsonify({
                    'code': 404,
                    'code_status': 'data not found',
                    'data': 'no referrals was found'
                }), 404

            data = []

            for referral in referrals:
                data.append({
                    'id': referral.id,
                    'referral_id': referral.referral_id,
                    'referral_code': referral.referral_code,
                    'referred_id': referral.referred_id,
                    'referred_code': referral.referred_code,
                    'created_at': referral.created_at,
                    'updated_at': referral.updated_at
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

        referral = ReferralModel.query.filter_by(id=id).first()

        try:
            if not referral:
                return jsonify({
                    'code': 404,
                    'code_status': 'data not found',
                    'data': 'no referral was found'
                }), 404

            data = {
                'id': referral.id,
                'referral_id': referral.referral_id,
                'referral_code': referral.referral_code,
                'referred_id': referral.referred_id,
                'referred_code': referral.referred_code,
                'created_at': referral.created_at,
                'updated_at': referral.updated_at
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
