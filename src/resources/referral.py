"""

"""
from hmac import compare_digest

from flask import jsonify, request

import config
from flask_restful import Resource
from sqlalchemy.exc import DataError, \
    DisconnectionError, \
    IntegrityError, \
    InternalError, \
    OperationalError, \
    ProgrammingError, \
    SQLAlchemyError

from ..models import ReferralModel, UserModel, db
from ..services import registration


class ReferralResource(Resource):
    """  """

    @staticmethod
    def create():
        """  """

        try:

            referral_id = request.json.get('referral_id')
            referred_id = request.json.get('referred_id')
            email_address = request.json.get('email_address')
            created_by_payverve = request.json.get('created_by_payverve')

            referred = UserModel.query.filter_by(
                id=referred_id, email_address=email_address).first()

            if not referred:
                return jsonify({
                    'code': 404,
                    'status_message': 'not found',
                    'message': 'user not found'
                }), 404

            # created_by_payverve is supplied by the caller, so on its own it
            # authenticated nothing: this route has no jwt_required, and anyone
            # who knew the URL could POST it with two user ids and mint 500 into
            # each wallet, repeatedly. The shared secret is what actually
            # establishes that Payverve itself is the caller. Fails closed.
            expected_secret = getattr(config, 'internal_api_secret', None)
            header_name = getattr(
                config, 'internal_api_secret_header', 'X-Payverve-Internal')
            sent_secret = request.headers.get(header_name)

            if not expected_secret:
                print('[referral] INTERNAL_API_SECRET is not set; rejecting. '
                      'Referrals cannot be created until it is configured.')
                return jsonify({
                    'code': 403,
                    'status_message': 'forbidden',
                    'message': 'you are not allowed to create a referral'
                }), 403

            if not sent_secret or not compare_digest(sent_secret.strip(),
                                                     expected_secret):
                print('[referral] rejected: bad or missing internal secret')
                return jsonify({
                    'code': 403,
                    'status_message': 'forbidden',
                    'message': 'you are not allowed to create a referral'
                }), 403

            if not created_by_payverve:
                return jsonify({
                    'code': 403,
                    'status_message': 'forbidden',
                    'message': 'you are not allowed to create a referral'
                }), 403

            referrer = UserModel.query.filter_by(id=referral_id).first()

            if not referrer:
                return jsonify({
                    'code': 404,
                    'status_message': 'not found',
                    'message': 'referrer not found'
                }), 404

            # Same code path registration uses, so the two cannot drift.
            try:
                registration.stage_referral(referrer, referred)
                db.session.commit()
            except registration.RegistrationError as e:
                db.session.rollback()
                return jsonify(e.as_payload()), e.code

            return jsonify({
                'code': 201,
                'status_message': 'created',
                'message': 'referral successfully registered'
            }), 201

        except IntegrityError:
            # Unwind the credits; the commit above is the only writer now.
            db.session.rollback()
            return jsonify({
                'code': 409,
                'status_message': 'conflict - integrity error',
                'message': 'this currency has already been listed'
            }), 409

        except DataError:
            # Unwind the credits; the commit above is the only writer now.
            db.session.rollback()
            return jsonify({
                'code': 400,
                'status_message': 'bad request - data error',
                'message': 'ensure input data are correct'
            }), 400

        except InternalError:
            # Unwind the credits; the commit above is the only writer now.
            db.session.rollback()
            return jsonify({
                'code': 500,
                'status_message': 'internal server - internal server error',
                'message': 'could not fetch data'
            }), 500

        except (OperationalError, DisconnectionError, SQLAlchemyError):
            # Unwind the credits; the commit above is the only writer now.
            db.session.rollback()
            return jsonify({
                'code': 500,
                'status_message': 'database error - operation, sqlalchemy and disconnection error',
                'message': 'could not fetch data'
            }), 500

        except ProgrammingError:
            # Unwind the credits; the commit above is the only writer now.
            db.session.rollback()
            return jsonify({
                'code': 500,
                'status_message': 'database error - programming error',
                'message': 'could not fetch table'
            }), 500

        except (ArithmeticError, ValueError, ZeroDivisionError):
            # Unwind the credits; the commit above is the only writer now.
            db.session.rollback()
            return jsonify({
                'code': 500,
                'status_message': 'calculation error - arithmetic, value, zerodivision error',
                'message': 'could run an arithmetic calculation'
            }), 500

    @staticmethod
    def read_all():
        """  """

        referrals = ReferralModel.query.all()

        try:
            if not referrals:
                return jsonify({
                    'code': 404,
                    'status_message': 'data not found',
                    'message': 'no referrals was found'
                }), 404

            data = []

            for referral in referrals:
                data.append({
                    'id': referral.id,
                    'referral_id': referral.referral_id,
                    'referral_code': referral.referral_code,
                    'referred_id': referral.referred_id,
                    'referred_code': referral.referred_code,
                    'created_at': referral.created_at.strftime("%d %b %Y, %I:%M %p"),
                    'updated_at': referral.updated_at.strftime("%d %b %Y, %I:%M %p") if referral.updated_at else None,
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

        referral = ReferralModel.query.filter_by(id=id).first()

        try:
            if not referral:
                return jsonify({
                    'code': 404,
                    'status_message': 'data not found',
                    'message': 'no referral was found'
                }), 404

            data = {
                'id': referral.id,
                'referral_id': referral.referral_id,
                'referral_code': referral.referral_code,
                'referred_id': referral.referred_id,
                'referred_code': referral.referred_code,
                'created_at': referral.created_at.strftime("%d %b %Y, %I:%M %p"),
                'updated_at': referral.updated_at.strftime("%d %b %Y, %I:%M %p") if referral.updated_at else None,
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
