"""

"""
from datetime import datetime
from hmac import compare_digest

from flask import jsonify
from psycopg2 import InternalError, OperationalError, ProgrammingError
from sqlalchemy import func
from sqlalchemy.exc import DisconnectionError

from . import Cryptographer
from ..models import KYCModel, LocalTransferModel, PayverveTransferModel


class KYCTierCheck:
    """ """

    @staticmethod
    def kyc_transfer_check(user_id, amount, transfer_type):
        """ """

        try:

            kyc_model = KYCModel.query.filter_by(user_id=user_id).first()

            if not kyc_model:
                return jsonify({
                    'code': 404,
                    'status_message': 'not found - kyc record not found',
                    'message': 'kyc record does not exist'
                }), 404

            kyc_tier = kyc_model.tier

            if compare_digest(str(kyc_tier), "0"):
                return jsonify({
                    'code': 403,
                    'status_message': 'forbidden - kyc tier is 0',
                    'message': 'you must be kyc tier 1 to make transfers.'
                }), 403

            if not compare_digest(str(kyc_tier), "3") and compare_digest(str(transfer_type), "international"):
                return jsonify({
                    'code': 403,
                    'status_message': 'forbidden - kyc tier is 1',
                    'message': 'you must be kyc tier 3 to make international transfers.'
                }), 403

            # @TODO: currency conversion to check other tier in international transfer

            if compare_digest(str(kyc_tier), "1") and transfer_type in ["local", "payverve"]:
                if float(amount) > float(50000):
                    return jsonify({
                        'code': 403,
                        'status_message': 'forbidden - kyc tier is 1',
                        'message': 'you can not transfer more than ₦50,000 at once and more than ₦300,000 in a day.'
                    }), 403

                today = datetime.now().date()
                sum_all_transfers = 0

                if compare_digest(str(transfer_type), "payverve"):
                    sum_transfers = (
                        PayverveTransferModel.query.filter(
                            PayverveTransferModel.user_id == user_id,
                            func.date(PayverveTransferModel.created_at) == today
                        )
                        .all()
                    )

                    for row in sum_transfers:
                        decrypted_amount = float(Cryptographer.decrypt(row.amount))  # this must return an int/float
                        sum_all_transfers += decrypted_amount

                if compare_digest(str(transfer_type), "local"):
                    sum_transfers = (
                        LocalTransferModel.query.filter(
                            LocalTransferModel.user_id == user_id,
                            func.date(LocalTransferModel.created_at) == today
                        )
                        .all()
                    )

                    for row in sum_transfers:
                        decrypted_amount = float(Cryptographer.decrypt(row.amount))  # this must return an int/float
                        sum_all_transfers += decrypted_amount

                if (float(sum_all_transfers) + float(amount)) > float(300000):
                    return jsonify({
                        'code': 403,
                        'status_message': 'forbidden - kyc tier is 1',
                        'message': 'you have exhauted your transfer limited for today.'
                    }), 403

            if compare_digest(str(kyc_tier), "2") and transfer_type in ["local", "payverve"]:
                if float(amount) > float(100000):
                    return jsonify({
                        'code': 403,
                        'status_message': 'forbidden - kyc tier is 2',
                        'message': 'you can not transfer more than ₦100,000 at once and more than ₦500,000 in a day.'
                    }), 403

                today = datetime.now().date()
                sum_all_transfers = 0

                if compare_digest(str(transfer_type), "payverve"):
                    sum_transfers = (
                        PayverveTransferModel.query.filter(
                            PayverveTransferModel.user_id == user_id,
                            func.date(PayverveTransferModel.created_at) == today
                        )
                        .all()
                    )

                    for row in sum_transfers:
                        decrypted_amount = float(Cryptographer.decrypt(row.amount))  # this must return an int/float
                        sum_all_transfers += decrypted_amount

                if compare_digest(str(transfer_type), "local"):
                    sum_transfers = (
                        LocalTransferModel.query.filter(
                            LocalTransferModel.user_id == user_id,
                            func.date(LocalTransferModel.created_at) == today
                        )
                        .all()
                    )

                    for row in sum_transfers:
                        decrypted_amount = float(Cryptographer.decrypt(row.amount))  # this must return an int/float
                        sum_all_transfers += decrypted_amount

                if (float(sum_all_transfers) + float(amount)) > float(500000):
                    return jsonify({
                        'code': 403,
                        'status_message': 'forbidden - kyc tier is 1',
                        'message': 'you have exhauted your transfer limited for today.'
                    }), 403

            if compare_digest(str(kyc_tier), "3") and transfer_type in ["local", "payverve"]:
                if float(amount) > float(5000000):
                    return jsonify({
                        'code': 403,
                        'status_message': 'forbidden - kyc tier is 2',
                        'message': 'you can not transfer more than ₦5,000,000 at once and more than ₦25,000,000 in a day.'
                    }), 403

                today = datetime.now().date()
                sum_all_transfers = 0

                if compare_digest(str(transfer_type), "payverve"):
                    sum_transfers = (
                        PayverveTransferModel.query.filter(
                            PayverveTransferModel.user_id == user_id,
                            func.date(PayverveTransferModel.created_at) == today
                        )
                        .all()
                    )

                    for row in sum_transfers:
                        decrypted_amount = float(Cryptographer.decrypt(row.amount))  # this must return an int/float
                        sum_all_transfers += decrypted_amount

                if compare_digest(str(transfer_type), "local"):
                    sum_transfers = (
                        LocalTransferModel.query.filter(
                            LocalTransferModel.user_id == user_id,
                            func.date(LocalTransferModel.created_at) == today
                        )
                        .all()
                    )

                    for row in sum_transfers:
                        decrypted_amount = float(Cryptographer.decrypt(row.amount))  # this must return an int/float
                        sum_all_transfers += decrypted_amount

                if (float(sum_all_transfers) + float(amount)) > float(5000000):
                    return jsonify({
                        'code': 403,
                        'status_message': 'forbidden - kyc tier is 1',
                        'message': 'you have exhauted your transfer limited for today.'
                    }), 403

            return None

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
    def kyc_balance_check(user_id, balance, transfer_type):
        """ """

        try:

            kyc_model = KYCModel.query.filter_by(user_id=user_id).first()

            if not kyc_model:
                return jsonify({
                    'code': 404,
                    'status_message': 'not found - kyc record not found',
                    'message': 'kyc record does not exist'
                }), 404

            kyc_tier = kyc_model.tier

            if compare_digest(str(kyc_tier), "0"):
                return jsonify({
                    'code': 403,
                    'status_message': 'forbidden - kyc tier is 0',
                    'message': 'you must be kyc tier 1 to make transfers.'
                }), 403

            if not compare_digest(str(kyc_tier), "3") and compare_digest(str(transfer_type), "international"):
                return jsonify({
                    'code': 403,
                    'status_message': 'forbidden - kyc tier is 1',
                    'message': 'you must be kyc tier 3 to make international transfers.'
                }), 403

            # @TODO: currency conversion to check other tier in international transfer

            if compare_digest(str(kyc_tier), "1") and compare_digest(str(transfer_type), "local") or compare_digest(str(
                    kyc_tier), "1") and compare_digest(str(transfer_type), "payverve"):
                if float(balance) > float(300000):
                    return jsonify({
                        'code': 403,
                        'status_message': 'forbidden',
                        'message': 'receipient can not receive this money at the moment.'
                    }), 403

            if compare_digest(str(kyc_tier), "2") and compare_digest(str(transfer_type), "local") or compare_digest(str(
                    kyc_tier), "2") and compare_digest(str(transfer_type), "payverve"):
                if float(balance) > float(500000):
                    return jsonify({
                        'code': 403,
                        'status_message': 'forbidden',
                        'message': 'receipient can not receive this money at the moment.'
                    }), 403

            return None

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
