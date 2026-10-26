"""

"""
from hmac import compare_digest

from flask import jsonify
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
from ..auth import (caller_id, caller_is_admin, forbidden, not_found, owns)
from ..middlewares import BellbankHelper
from ..models import LocalTransferModel, SpendSaveModel, TransactionModel, UserModel, WalletModel, db
from ..services import transfer_status
from ..services.transfer_status import normalise_status as _normalise_status
from ..utilities import Cryptographer, KYCTierCheck, RandomGenerator, parse_params


def _bank_message(response, default):
    try:
        return (response.json() or {}).get('message') or default
    except ValueError:
        return default


def _transfer_outcome(response, reference, access_token):
    """Decide what happened to a transfer: successful, pending or failed.

    'failed' means the money certainly did not leave and is refunded. When
    that cannot be known -- the request errored in flight, or BellBank
    answered 5xx -- the transfer is asked about by reference, and if that
    is inconclusive too it stays pending with the money reserved, because
    refunding a transfer that did go through would pay it out twice.
    """
    if not access_token:
        return {'status': 'failed', 'data': {},
                'message': 'could not reach the bank'}

    if response is not None and 200 <= response.status_code < 300:
        try:
            data = (response.json() or {}).get('data') or {}
        except ValueError:
            data = {}
        return {'status': _normalise_status(data.get('status')), 'data': data,
                'message': ''}

    if response is not None and 400 <= response.status_code < 500:
        return {'status': 'failed', 'data': {},
                'message': _bank_message(response, 'the bank refused the '
                                                   'transfer')}

    requery = BellbankHelper.transfer_requery(reference, access_token)

    if requery is not None and requery.status_code == 200:
        try:
            data = (requery.json() or {}).get('data') or {}
        except ValueError:
            data = {}
        if data:
            return {'status': _normalise_status(data.get('status'),
                                                data.get('reversedFlag')),
                    'data': data, 'message': ''}

    print(f'[transfer] {reference}: outcome unknown, left pending with the '
          'money reserved; requery it before refunding')
    return {'status': 'pending', 'data': {}, 'message': ''}


def _refund(transfer_id, history_id, wallet_id, amount_value):
    """Give a refused transfer's money back and mark it failed, together."""
    wallet = WalletModel.query.filter_by(id=wallet_id).with_for_update().one()
    wallet.fund = Cryptographer.encrypt(
        float(Cryptographer.decrypt(wallet.fund)) + amount_value)
    db.session.get(LocalTransferModel, transfer_id).transaction_status = \
        'failed'
    db.session.get(TransactionModel, history_id).status = 'failed'
    db.session.commit()


def _spend_and_save(user_id, wallet_id, amount_value, owner_name):
    """Move the customer's Spend & Save percentage of a transfer to savings.

    This used to add the percentage to the savings balance without taking it
    out of the wallet, so every transfer created that money from nothing.
    Best effort: the transfer has already happened and must not be undone
    by a savings failure.
    """
    try:
        spend_save = SpendSaveModel.query.filter_by(user_id=user_id).first()

        if not spend_save or not spend_save.is_active:
            return

        to_save = round(amount_value * float(spend_save.percentage_to_save)
                        / 100, 2)

        if to_save <= 0:
            return

        wallet = WalletModel.query.filter_by(
            id=wallet_id).with_for_update().one()
        balance = float(Cryptographer.decrypt(wallet.fund))

        if balance < to_save:
            db.session.rollback()
            return

        wallet.fund = Cryptographer.encrypt(balance - to_save)
        spend_save.balance = Cryptographer.encrypt(
            float(Cryptographer.decrypt(spend_save.balance)) + to_save)

        # noinspection PyArgumentList
        db.session.add(TransactionModel(
            amount=Cryptographer.encrypt(f'{to_save:.2f}'),
            transaction_type='spend_and_save',
            user_id=user_id,
            currency_id=wallet.currency_id,
            note=f"{spend_save.percentage_to_save}% of this transaction was "
                 f"saved under Spend & Save plan",
            status='successful',
            name=owner_name,
            transaction_flow='debit',
            transaction_title='Money Saved',
            currency_ticker='ngn'
        ))
        db.session.commit()

        NotificationResource.store_nofication(
            title="Spend Save",
            body=f"₦{to_save:,.2f} was saved under Spend & Save plan",
            user_id=user_id,
        )
    except Exception as e:  # noqa: BLE001
        db.session.rollback()
        print(f'[transfer] spend & save skipped: {type(e).__name__}: {e}')


class LocalTransferResource(Resource):
    """ This class is concern with Local Transfer Resources """

    @staticmethod
    @parse_params(
        Argument("account", location="json", type=int, required=True),
        Argument("bank_code", location="json", type=str, required=True),
        Argument("bank_name", location="json", required=True),
    )
    def resolve_account(account, bank_code, bank_name):
        """ Resolve bank account details """

        try:

            if not bank_name:
                return jsonify({
                    'code': 400,
                    'status_message': 'bad request',
                    'message': 'bank name is required'
                }), 400

            if not account:
                return jsonify({
                    'code': 400,
                    'status_message': 'bad request',
                    'message': 'account number is required'
                }), 400

            if not bank_code:
                return jsonify({
                    'code': 400,
                    'status_message': 'bad request',
                    'message': 'bank code is required'
                }), 400

            access_token = BellbankHelper.bellbank_authentication('5')
            response = BellbankHelper.bell_resolve_account_number(
                account, bank_code, access_token)

            if response is None:
                return jsonify({
                    'code': 502,
                    'status_message': 'bad gateway',
                    'message': 'could not reach the bank to resolve that account'
                }), 502

            if not compare_digest(str(response.status_code), '200'):
                return jsonify({
                    'code': response.status_code,
                    'status_message': 'failed to resolve bank account',
                    'message': response.json().get('message', 'an error occurred while resolving bank account')
                }), response.status_code

            bank_data = response.json().get('data', {})

            final_data = {
                'bank_name': bank_name,
                'account_number': account,
                'account_name': bank_data.get('accountName'),
            }

            return jsonify({
                'code': 200,
                'status_message': 'success',
                'data': final_data
            }), 200

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
    @parse_params(
        Argument("bank_code", location="json", required=True),
        Argument("amount", location="json", required=True),
        Argument("narration", location="json", required=True),
        Argument("account_number", location="json", required=True),
        Argument("recipient_name", location="json", required=True),
        Argument("recipient_bank", location="json", required=True),
        Argument("user_id", location="json", required=True),
        Argument("wallet_id", location="json", required=True),
    )
    def create(bank_code, amount, narration, account_number, recipient_name, recipient_bank, user_id, wallet_id):
        """ """

        try:

            # user_id arrives in the request body, and the only check below
            # was that wallet_id belongs to it -- both caller-supplied and
            # self-consistent, so pointing this at another customer's
            # user_id and wallet_id moved their money to any bank account.
            # GET /wallets handed out exactly those two ids. Authorise
            # against the token instead; the body value is now only
            # accepted when it agrees with it.
            if not owns(user_id):
                return forbidden(
                    'you cannot transfer from another customer wallet')

            # KYC Tier Check
            kyc_check = KYCTierCheck.kyc_transfer_check(
                user_id, amount, 'local')
            if kyc_check is not None:
                return kyc_check

            user_check = UserModel.query.filter_by(id=user_id).first()

            if not user_check:
                return jsonify({
                    'code': 404,
                    'status_message': 'data not found',
                    'message': 'user not found'
                }), 404

            wallet_check = WalletModel.query.filter_by(id=wallet_id).first()

            if not wallet_check:
                return jsonify({
                    'code': 404,
                    'status_message': 'data not found',
                    'message': 'wallet not found'
                }), 404

            if not compare_digest(str(wallet_check.user_id), str(user_id)):
                return jsonify({
                    'code': 403,
                    'status_message': 'forbidden',
                    'message': 'you do not have access to this wallet'
                }), 403

            if not compare_digest(str(wallet_check.currency_ticker).lower(), 'ngn'):
                return jsonify({
                    'code': 400,
                    'status_message': 'bad request',
                    'message': 'local transfers can only be made from NGN wallets'
                }), 400

            decrypt_fund = Cryptographer.decrypt(wallet_check.fund)

            if float(decrypt_fund) < float(amount):
                return jsonify({
                    'code': 400,
                    'status_message': 'bad request',
                    'message': 'insufficient funds'
                }), 400

            # The money is reserved BEFORE the bank is asked to move it, and
            # every balance change happens on a locked, freshly read wallet.
            #
            # This used to read the balance, call BellBank, and then write
            # back (balance read earlier - amount): a deposit credited during
            # the call was wiped out, and two sends at once could both pass the
            # balance check. After the bank accepted, it read
            # wallet.account_number -- a column wallets no longer have -- so
            # every successful transfer raised a 500 with the money already
            # gone and nothing recorded, inviting the customer to send again.
            sender_name = f"{user_check.first_name} {user_check.last_name}"
            amount_value = round(float(amount), 2)

            if amount_value <= 0:
                return jsonify({
                    'code': 400,
                    'status_message': 'bad request',
                    'message': 'amount must be greater than zero'
                }), 400

            reference_number = RandomGenerator.local_transfer_reference_number()
            sender_account = BellbankHelper.virtual_account_for_wallet(
                wallet_check)

            wallet = WalletModel.query.filter_by(
                id=wallet_id).with_for_update().one()

            if float(Cryptographer.decrypt(wallet.fund)) < amount_value:
                db.session.rollback()
                return jsonify({
                    'code': 400,
                    'status_message': 'bad request',
                    'message': 'insufficient funds'
                }), 400

            wallet.fund = Cryptographer.encrypt(
                float(Cryptographer.decrypt(wallet.fund)) - amount_value)

            # noinspection PyArgumentList
            local_transfer = LocalTransferModel(
                amount=Cryptographer.encrypt(f'{amount_value:.2f}'),
                charge_amount=0.0,
                sender_name=sender_name,
                sender_account_number=int(sender_account or 0),
                narration=narration,
                recipient_name=recipient_name,
                recipient_bank=recipient_bank,
                recipient_account_number=account_number,
                reference_number=reference_number,
                # Unique and required, but BellBank only assigns a session id
                # once it accepts the transfer. The reference stands in until
                # then.
                session_id=reference_number,
                stamp_duty=0.0,
                sender_bank="bellbank microfinance bank",
                user_id=user_id,
                wallet_id=wallet_id,
                transaction_status='pending',
            )
            db.session.add(local_transfer)

            # noinspection PyArgumentList
            history = TransactionModel(
                # Links the history row to its transfer, so settling a
                # pending transfer later can update both.
                tx_ref=reference_number,
                amount=Cryptographer.encrypt(f'{amount_value:.2f}'),
                transaction_type='domestic_transfer',
                user_id=user_id,
                currency_id=wallet.currency_id,
                note=narration,
                status='pending',
                name=recipient_name,
                transaction_flow='debit',
                transaction_title='Money Sent',
                currency_ticker='ngn'
            )
            db.session.add(history)
            db.session.commit()

            access_token = BellbankHelper.bellbank_authentication('6')
            transfer_response = None

            if access_token:
                transfer_response = BellbankHelper.transfer_outbound(
                    bank_code=bank_code,
                    amount=f'{amount_value:.2f}',
                    narration=narration,
                    account_number=account_number,
                    reference=reference_number,
                    sender_name=sender_name,
                    recipient_name=recipient_name,
                    access_token=access_token
                )

            outcome = _transfer_outcome(transfer_response, reference_number,
                                        access_token)

            if outcome['status'] == 'failed':
                _refund(local_transfer.id, history.id, wallet_id, amount_value)
                print(f'[transfer] {reference_number} refused by the bank, '
                      f'refunded: {outcome["message"]}')
                return jsonify({
                    'code': 400,
                    'status_message': 'transfer failed',
                    'message': f'{outcome["message"]}; no money has left '
                               f'your wallet'
                }), 400

            local_transfer = db.session.get(LocalTransferModel,
                                            local_transfer.id)
            history = db.session.get(TransactionModel, history.id)
            data = outcome['data']
            local_transfer.transaction_status = outcome['status']
            history.status = outcome['status']
            local_transfer.charge_amount = float(data.get('charge') or 0)

            if data.get('sessionId'):
                local_transfer.session_id = str(data['sessionId'])

            db.session.commit()
            print(f'[transfer] {reference_number}: {outcome["status"]} '
                  f'(₦{amount_value:,.2f} to {account_number})')

            try:
                NotificationResource.store_and_push(
                    title="Local Transfer",
                    body=f"₦{amount_value:,.2f} was sent to {recipient_name}",
                    user_id=user_id,
                    data={"type": "wallet_debit",
                          "amount": f'{amount_value:.2f}'},
                )
            except Exception as e:  # noqa: BLE001 - the transfer stands
                print(f'[transfer] notification failed for '
                      f'{reference_number}: {type(e).__name__}: {e}')

            _spend_and_save(user_id, wallet_id, amount_value, sender_name)

            processing = outcome['status'] != 'successful'

            return jsonify({
                'code': 201,
                'status_message': 'created',
                'message': 'transfer is still processing' if processing
                else 'transfer was done successfully',
                'data': {'reference': reference_number,
                         'status': outcome['status']},
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
        """ Retrieve all local transfers """

        local_transfers = LocalTransferModel.query.order_by(
            LocalTransferModel.created_at.desc()).all()
        # Was an unscoped dump of every row to any signed-in customer.
        # Filtered on the result rather than in the query so the existing
        # ordering and shape are untouched; these tables are small.
        if not caller_is_admin():
            _me = caller_id()
            local_transfers = [r for r in local_transfers
                      if str(getattr(r, 'user_id', None)) == _me]


        try:
            if not local_transfers:
                return jsonify({
                    'code': 404,
                    'status_message': 'data not found',
                    'message': 'no local transfer history was found'
                }), 404

            data = []

            for local_transfer in local_transfers:
                data.append({
                    'id': local_transfer.id,
                    'amount': Cryptographer.decrypt(local_transfer.amount),
                    'charge_amount': local_transfer.charge_amount,
                    'sender_name': local_transfer.sender_name,
                    'sender_bank': local_transfer.sender_bank,
                    'sender_account_number': local_transfer.sender_account_number,
                    'narration': local_transfer.narration,
                    'recipient_name': local_transfer.recipient_name,
                    'recipient_bank': local_transfer.recipient_bank,
                    'recipient_account_number': local_transfer.recipient_account_number,
                    'reference_number': local_transfer.reference_number,
                    'session_id': local_transfer.session_id,
                    'stamp_duty': local_transfer.stamp_duty,
                    'transfer_type': local_transfer.transfer_type,
                    'transfer_pair': local_transfer.transfer_pair,
                    'transaction_status': local_transfer.transaction_status,
                    'user_id': local_transfer.user_id,
                    'wallet_id': local_transfer.wallet_id,
                    'created_at': local_transfer.created_at.strftime("%d %b %Y, %I:%M %p"),
                    'updated_at': local_transfer.updated_at.strftime("%d %b %Y, %I:%M %p") if local_transfer.updated_at else None,
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
    def refresh_status(id=None):
        """Ask BellBank what became of a pending transfer, and apply it.

        A failed or reversed transfer is refunded here; a completed one is
        marked successful. Safe to call repeatedly, from the app or anywhere.
        """
        transfer = LocalTransferModel.query.filter_by(id=id).first()

        # Someone else's transfer is reported as missing, not as forbidden.
        if transfer is None or not owns(transfer.user_id):
            return not_found('no transfer was found')

        try:
            result = transfer_status.settle_transfer(transfer.id)
        except Exception as e:  # noqa: BLE001
            db.session.rollback()
            print(f'[transfer] status refresh failed for '
                  f'{transfer.reference_number}: {type(e).__name__}: {e}')
            return jsonify({
                'code': 502,
                'status_message': 'bad gateway',
                'message': 'could not check the transfer with the bank; '
                           'try again shortly'
            }), 502

        messages = {
            'successful': 'transfer was done successfully',
            'failed': 'transfer failed; the money is back in your wallet',
            'pending': 'transfer is still processing',
        }

        return jsonify({
            'code': 200,
            'status_message': 'success',
            'message': messages.get(result['now'], result['now']),
            'data': {'reference': result['reference'],
                     'status': result['now'],
                     'refunded': result['refunded']},
        }), 200

    @staticmethod
    def read_one(id=None):
        """  """

        local_transfer = LocalTransferModel.query.filter_by(id=id).first()

        try:
            # the id in the path was trusted outright, with no check that it belongs to the caller.
            _owner = LocalTransferModel.query.filter_by(id=id).first()
            if _owner is not None and not owns(_owner.user_id):
                return not_found(
                    'no transfer was found')

            if not local_transfer:
                return jsonify({
                    'code': 404,
                    'status_message': 'data not found',
                    'message': 'no local transfer was found'
                }), 404

            data = {
                'id': local_transfer.id,
                'amount': Cryptographer.decrypt(local_transfer.amount),
                'charge_amount': local_transfer.charge_amount,
                'sender_name': local_transfer.sender_name,
                'sender_bank': local_transfer.sender_bank,
                'sender_account_number': local_transfer.sender_account_number,
                'narration': local_transfer.narration,
                'recipient_name': local_transfer.recipient_name,
                'recipient_bank': local_transfer.recipient_bank,
                'recipient_account_number': local_transfer.recipient_account_number,
                'reference_number': local_transfer.reference_number,
                'session_id': local_transfer.session_id,
                'stamp_duty': local_transfer.stamp_duty,
                'transfer_type': local_transfer.transfer_type,
                'transfer_pair': local_transfer.transfer_pair,
                'transaction_status': local_transfer.transaction_status,
                'user_id': local_transfer.user_id,
                'wallet_id': local_transfer.wallet_id,
                'created_at': local_transfer.created_at.strftime("%d %b %Y, %I:%M %p"),
                'updated_at': local_transfer.updated_at.strftime("%d %b %Y, %I:%M %p") if local_transfer.updated_at else None,
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
    def user_ltf_all(id):
        """ Retrieve all local transfers """

        local_transfers = LocalTransferModel.query.filter_by(
            user_id=id).order_by(LocalTransferModel.created_at.desc()).all()

        try:
            # the id in the path was trusted outright, with no check that it belongs to the caller.
            if not owns(id):
                return not_found(
                    'no transfer was found')

            if not local_transfers:
                return jsonify({
                    'code': 404,
                    'status_message': 'data not found',
                    'message': 'no local transfer history was found'
                }), 404

            data = []

            for local_transfer in local_transfers:
                data.append({
                    'id': local_transfer.id,
                    'amount': Cryptographer.decrypt(local_transfer.amount),
                    'charge_amount': local_transfer.charge_amount,
                    'sender_name': local_transfer.sender_name,
                    'sender_bank': local_transfer.sender_bank,
                    'sender_account_number': local_transfer.sender_account_number,
                    'narration': local_transfer.narration,
                    'recipient_name': local_transfer.recipient_name,
                    'recipient_bank': local_transfer.recipient_bank,
                    'recipient_account_number': local_transfer.recipient_account_number,
                    'reference_number': local_transfer.reference_number,
                    'session_id': local_transfer.session_id,
                    'stamp_duty': local_transfer.stamp_duty,
                    'transfer_type': local_transfer.transfer_type,
                    'transfer_pair': local_transfer.transfer_pair,
                    'transaction_status': local_transfer.transaction_status,
                    'user_id': local_transfer.user_id,
                    'wallet_id': local_transfer.wallet_id,
                    'created_at': local_transfer.created_at.strftime("%d %b %Y, %I:%M %p"),
                    'updated_at': local_transfer.updated_at.strftime("%d %b %Y, %I:%M %p") if local_transfer.updated_at else None,
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
