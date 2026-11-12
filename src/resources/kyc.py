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

from .notification import NotificationResource
from ..middlewares import verify_bvn_identity
from ..models import AdminModel, KYCModel, UserModel
from ..services import registration, virtual_account
from ..utilities import (encrypt_identifier, hash_identifier,
                         parse_params)
from ..value_object import BVNCheck, NINCheck


def _caller_id():
    """The authenticated subject, as jwt_required recorded it."""
    current = getattr(request, 'current_user', None) or {}
    return str(current.get('sub') or '')


def _caller_is_admin():
    """Whether the caller is an admin rather than a customer.

    jwt_required admits customers and admins alike and records no role,
    so the distinction has to be re-established here. There is no
    admin-only decorator in this codebase to lean on.
    """
    caller = _caller_id()

    if not caller:
        return False

    return AdminModel.query.filter_by(id=caller).first() is not None


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
            full_name = request.json.get('full_name')
            mobile_number = request.json.get('mobile_number')

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

            if full_name is None:
                return jsonify({
                    'code': 400,
                    'status_message': 'bad request',
                    'message': 'full name is required to create kyc'
                }), 400

            if mobile_number is None:
                return jsonify({
                    'code': 400,
                    'status_message': 'bad request',
                    'message': 'mobile number is required to create kyc'
                }), 400

            # noinspection PyArgumentList
            new_kyc = KYCModel(
                user_id=user_id,
                full_name_present=True,
                phone_number_present=True,
            )
            new_kyc.save()

            return jsonify({
                'code': 201,
                'status_message': 'created',
                'message': 'kyc successfully initiated'
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
        """Every KYC record for an admin; your own if you are a customer.

        This returned KYCModel.query.all() behind nothing but
        jwt_required, so any signed-in customer could read every other
        customer's bvn, nin, address and selfie in one request.
        """

        if _caller_is_admin():
            kycs = KYCModel.query.all()
        else:
            kycs = KYCModel.query.filter_by(user_id=_caller_id()).all()

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
                    # Deliberately absent: the identifier itself is never
                    # returned. bvn_present / nin_present below carry
                    # everything the client needs to render KYC state.
                    'selfie': kyc.selfie,
                    'address': kyc.address,
                    'bvn_present': kyc.bvn_present,
                    'nin_present': kyc.nin_present,
                    'full_name_present': kyc.full_name_present,
                    'selfie_present': kyc.selfie_present,
                    'phone_number_present': kyc.phone_number_present,
                    'address_present': kyc.address_present,
                    'user_id': kyc.user_id,
                    'created_at': kyc.created_at.strftime("%d %b %Y, %I:%M %p"),
                    'updated_at': kyc.updated_at.strftime("%d %b %Y, %I:%M %p") if kyc.updated_at else None,
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

            # There was no ownership check here, so any signed-in customer
            # could read any KYC record by its id. 404 rather than 403: a
            # 403 would confirm the record exists, which is the thing an
            # enumerating caller is trying to learn.
            if not _caller_is_admin() and str(kyc.user_id) != _caller_id():
                return jsonify({
                    'code': 404,
                    'status_message': 'data not found',
                    'message': 'no kyc was found'
                }), 404

            data = {
                'id': kyc.id,
                'tier': kyc.tier,
                # Deliberately absent -- see read_all.
                'selfie': kyc.selfie,
                'address': kyc.address,
                'bvn_present': kyc.bvn_present,
                'nin_present': kyc.nin_present,
                'full_name_present': kyc.full_name_present,
                'selfie_present': kyc.selfie_present,
                'phone_number_present': kyc.phone_number_present,
                'address_present': kyc.address_present,
                'user_id': kyc.user_id,
                'created_at': kyc.created_at.strftime("%d %b %Y, %I:%M %p"),
                'updated_at': kyc.updated_at.strftime("%d %b %Y, %I:%M %p") if kyc.updated_at else None,
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
        Argument("selfie", location="json"),
        Argument("nin", location="json"),
        Argument("address", location="json"),
    )
    def update(id=None, **fields):
        """  """

        kyc = KYCModel.query.filter_by(user_id=id).first()

        # @TODO: use dojah for nin, selfie and bvn verification

        try:
            if not kyc:
                return jsonify({
                    'code': 404,
                    'status_message': 'data not found',
                    'message': 'the customer was not found'
                }), 404

            # The id in the path is a user_id and was trusted outright, so
            # any signed-in customer could write a bvn, nin or address onto
            # another customer KYC record -- and since bvn can be set only
            # once, doing so would lock the real owner out permanently.
            if not _caller_is_admin() and str(id) != _caller_id():
                return jsonify({
                    'code': 403,
                    'status_message': 'forbidden',
                    'message': 'you cannot update the kyc of another customer'
                }), 403

            if 'bvn' in fields and fields['bvn'] is not None:
                if kyc.bvn_present:
                    return jsonify({
                        'code': 400,
                        'status_message': 'bad request',
                        'message': 'bvn has already been updated if you want to update it, contact support'
                    }), 400

                if not kyc.full_name_present:
                    return jsonify({
                        'code': 400,
                        'status_message': 'bad request',
                        'message': 'ensure full name is has been added to your profile'
                    }), 400

                if not kyc.phone_number_present:
                    return jsonify({
                        'code': 400,
                        'status_message': 'bad request',
                        'message': 'ensure phone number is has been added to your profile and verified'
                    }), 400

                # if 'selfie' not in fields or fields['selfie'] is None:
                #     return jsonify({
                #         'code': 400,
                #         'status_message': 'bad request',
                #         'message': 'selfie is required to update bvn'
                #     }), 400

                BVNCheck(fields['bvn'])

                # Check the submitted identity against the BVN record
                # before anything is stored. BellBank runs this check
                # itself when it creates the client, but by then the
                # client exists and a mismatch can only be fixed by
                # deleting it -- the customer just sees inbound transfers
                # refused with 'KYC verification incomplete'. Catching it
                # here turns that into a form error they can correct.
                owner = UserModel.query.filter_by(id=kyc.user_id).first()
                identity = verify_bvn_identity(
                    fields['bvn'],
                    first_name=owner.first_name if owner else None,
                    last_name=owner.last_name if owner else None,
                    date_of_birth=owner.date_of_birth if owner else None,
                    gender=owner.gender if owner else None)

                if identity.checked and not identity.ok:
                    # Names the fields that disagree and never the values
                    # held against the bvn: returning those would make
                    # this endpoint a lookup service for any bvn.
                    wrong = ', '.join(
                        f.replace('_', ' ') for f in identity.mismatches)
                    return jsonify({
                        'code': 400,
                        'status_message': 'bad request',
                        'message': f'your {wrong} does not match your bvn '
                                   f'record, please correct it and try again',
                        'data': {'mismatched_fields': identity.mismatches}
                    }), 400

                # Uniqueness moved off the value column, which is now
                # ciphertext and cannot be constrained: Fernet is
                # non-deterministic. Check the keyed hash instead.
                bvn_hash = hash_identifier(fields['bvn'])

                taken = KYCModel.query.filter(
                    KYCModel.bvn_hash == bvn_hash,
                    KYCModel.user_id != kyc.user_id).first()

                if taken:
                    # Intentionally does not say the bvn is already
                    # registered: that answer turns this endpoint into an
                    # oracle for whether a given person banks here.
                    return jsonify({
                        'code': 409,
                        'status_message': 'conflict',
                        'message': 'we could not verify that bvn, please contact support'
                    }), 409

                kyc.bvn = encrypt_identifier(fields['bvn'])
                kyc.bvn_hash = bvn_hash
                # kyc.selfie = fields['selfie']
                kyc.bvn_present = True
                kyc.selfie_present = True
                kyc.tier = 1

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

                nin_hash = hash_identifier(fields['nin'])

                taken = KYCModel.query.filter(
                    KYCModel.nin_hash == nin_hash,
                    KYCModel.user_id != kyc.user_id).first()

                if taken:
                    return jsonify({
                        'code': 409,
                        'status_message': 'conflict',
                        'message': 'we could not verify that nin, please contact support'
                    }), 409

                kyc.nin = encrypt_identifier(fields['nin'])
                kyc.nin_hash = nin_hash
                kyc.nin_present = True
                kyc.tier = 2

                # if kyc.address_present:
                #     kyc.tier = 3

            if 'address' in fields and fields['address'] is not None:
                if kyc.address_present:
                    return jsonify({
                        'code': 400,
                        'status_message': 'bad request',
                        'message': 'address has already been updated if you want to update it, contact support'
                    }), 400

                if not kyc.bvn_present and fields['bvn'] is None:
                    return jsonify({
                        'code': 400,
                        'status_message': 'bad request',
                        'message': 'provide bvn to update address'
                    }), 400

                if not kyc.nin_present and fields['nin'] is None:
                    return jsonify({
                        'code': 400,
                        'status_message': 'bad request',
                        'message': 'provide nin to update address'
                    }), 400

                kyc.address = fields['address']
                kyc.address_present = True
                kyc.tier = 3

            kyc.save()

            get_tier = KYCModel.query.filter_by(user_id=id).first()

            NotificationResource.store_nofication(
                title="Account Upgrade",
                body=f"Your account has been upgraded to level {get_tier.tier}",
                user_id=kyc.user_id,
            )

            # Provisioning previously ran only at registration and wallet
            # creation, so anyone who supplied a bvn or address afterwards
            # never got an account number. Now that the details are on file,
            # retry it. Best effort on purpose: the KYC update itself has
            # already committed, and failing the whole request over the bank
            # would lose that.
            account_number = None

            if kyc.bvn_present and kyc.address_present:
                try:
                    issued = virtual_account.ensure_ngn_virtual_account(
                        kyc.user_id)
                    account_number = issued.account_number if issued else None
                except registration.RegistrationError as e:
                    print(f'[kyc] provisioning deferred for {kyc.user_id}: '
                          f'{e.as_payload()}')
                except Exception as e:  # noqa: BLE001 - never fail the update
                    print(f'[kyc] provisioning errored for {kyc.user_id}: '
                          f'{type(e).__name__}: {e}')

            return jsonify({
                'code': 200,
                'status_message': 'success',
                'message': "kyc successfully updated",
                'data': {'account_number': account_number}
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
