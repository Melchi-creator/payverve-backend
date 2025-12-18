"""

"""

from flask import jsonify
from flask_restful import Resource
from sqlalchemy.exc import DisconnectionError, \
    InternalError, \
    OperationalError, \
    ProgrammingError

from ..models import InboundTransferModel
from ..utilities import Cryptographer


class InboundTransferResource(Resource):
    """  """

    @staticmethod
    def read_all():
        """  """

        inbound_transfers = InboundTransferModel.query.order_by(InboundTransferModel.created_at.desc()).all()

        try:
            if not inbound_transfers:
                return jsonify({
                    'code': 404,
                    'status_message': 'data not found',
                    'message': 'no inbound transfer was found'
                }), 404

            data = []

            for inbound_transfer in inbound_transfers:
                data.append({
                    'id': inbound_transfer.id,
                    'amount': Cryptographer.decrypt(inbound_transfer.amount),
                    'charge_amount': inbound_transfer.charge_amount,
                    'sender_name': inbound_transfer.sender_name,
                    'sender_bank': inbound_transfer.sender_bank,
                    'sender_account_number': inbound_transfer.sender_account_number,
                    'narration': inbound_transfer.narration,
                    'recipient_name': inbound_transfer.reference,
                    'recipient_bank': inbound_transfer.recipient_bank,
                    'recipient_account_number': inbound_transfer.recipient_account_number,
                    'reference': inbound_transfer.reference,
                    'session_id': inbound_transfer.session_id,
                    'stamp_duty': inbound_transfer.stamp_duty,
                    'transaction_type': inbound_transfer.transaction_type,
                    'transfer_pair': inbound_transfer.transfer_pair,
                    'transaction_status': inbound_transfer.transaction_status,
                    'user_id': inbound_transfer.user_id,
                    'wallet_id': inbound_transfer.wallet_id,
                    'created_at': inbound_transfer.created_at.strftime("%d %b %Y, %I:%M %p"),
                    'updated_at': inbound_transfer.updated_at.strftime("%d %b %Y, %I:%M %p") if inbound_transfer.updated_at else None,
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
        """ Retrieve one inbound transfer by id """

        inbound_transfer = InboundTransferModel.query.filter_by(id=id).first()

        try:
            if not inbound_transfer:
                return jsonify({
                    'code': 404,
                    'status_message': 'data not found',
                    'message': 'no inbound transfer was found'
                }), 404

            data = {
                'id': inbound_transfer.id,
                'amount': Cryptographer.decrypt(inbound_transfer.amount),
                'charge_amount': inbound_transfer.charge_amount,
                'sender_name': inbound_transfer.sender_name,
                'sender_bank': inbound_transfer.sender_bank,
                'sender_account_number': inbound_transfer.sender_account_number,
                'narration': inbound_transfer.narration,
                'recipient_name': inbound_transfer.reference,
                'recipient_bank': inbound_transfer.recipient_bank,
                'recipient_account_number': inbound_transfer.recipient_account_number,
                'reference': inbound_transfer.reference,
                'session_id': inbound_transfer.session_id,
                'stamp_duty': inbound_transfer.stamp_duty,
                'transaction_type': inbound_transfer.transaction_type,
                'transfer_pair': inbound_transfer.transfer_pair,
                'transaction_status': inbound_transfer.transaction_status,
                'user_id': inbound_transfer.user_id,
                'wallet_id': inbound_transfer.wallet_id,
                'created_at': inbound_transfer.created_at.strftime("%d %b %Y, %I:%M %p"),
                'updated_at': inbound_transfer.updated_at.strftime("%d %b %Y, %I:%M %p") if inbound_transfer.updated_at else None,
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
    def user_ibtf_all(id=None):
        """ Retrieve all inbound transfer """

        inbound_transfers = InboundTransferModel.query.filter_by(user_id=id).order_by(InboundTransferModel.created_at.desc()).all()

        try:
            if not inbound_transfers:
                return jsonify({
                    'code': 404,
                    'status_message': 'data not found',
                    'message': 'no inbound transfer was found'
                }), 404

            data = []

            for inbound_transfer in inbound_transfers:
                data.append({
                    'id': inbound_transfer.id,
                    'amount': Cryptographer.decrypt(inbound_transfer.amount),
                    'charge_amount': inbound_transfer.charge_amount,
                    'sender_name': inbound_transfer.sender_name,
                    'sender_bank': inbound_transfer.sender_bank,
                    'sender_account_number': inbound_transfer.sender_account_number,
                    'narration': inbound_transfer.narration,
                    'recipient_name': inbound_transfer.reference,
                    'recipient_bank': inbound_transfer.recipient_bank,
                    'recipient_account_number': inbound_transfer.recipient_account_number,
                    'reference': inbound_transfer.reference,
                    'session_id': inbound_transfer.session_id,
                    'stamp_duty': inbound_transfer.stamp_duty,
                    'transaction_type': inbound_transfer.transaction_type,
                    'transfer_pair': inbound_transfer.transfer_pair,
                    'transaction_status': inbound_transfer.transaction_status,
                    'user_id': inbound_transfer.user_id,
                    'wallet_id': inbound_transfer.wallet_id,
                    'created_at': inbound_transfer.created_at.strftime("%d %b %Y, %I:%M %p"),
                    'updated_at': inbound_transfer.updated_at.strftime("%d %b %Y, %I:%M %p") if inbound_transfer.updated_at else None,
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

