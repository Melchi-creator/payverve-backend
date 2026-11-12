"""
src/resources/charge.py

Creating a charge, showing it to a buyer, and settling it.

Three audiences, three authentications:

  the shop's server   secret key    creates and verifies charges
  the buyer's browser charge_code   reads what to pay and how, no session
  the buyer in-app    jwt           pays from their Payverve wallet

The checkout read is deliberately unauthenticated: a buyer following a link
from a shop has no Payverve session yet. It therefore returns only what is
needed to pay -- amount, shop name, where to send money, how long is left --
and nothing about the shop's other charges or the buyer.
"""
import config
from flask import (current_app, jsonify, make_response, render_template,
                   request, url_for)
from flask_restful import Resource
from sqlalchemy.exc import (DataError, DisconnectionError, IntegrityError,
                            InternalError, OperationalError, ProgrammingError,
                            SQLAlchemyError)

from ..models import ChargeModel, MerchantModel, UserModel, db
from ..services import checkout, merchant_webhook
from ..services.registration import RegistrationError
from ..utilities import run_detached

DATABASE_ERRORS = (InternalError, OperationalError, DisconnectionError,
                   ProgrammingError, SQLAlchemyError)


def _deliver_in_app_context(app, delivery_id):
    """Send a queued webhook from a background thread.

    The app is passed in, not read from `current_app`: the thread outlives the
    request, so by the time this runs there is no request context to read it
    from. It makes its own app context, and therefore its own session.
    """
    with app.app_context():
        merchant_webhook.attempt(delivery_id)


def checkout_page_url(charge_code):
    """The absolute URL of the buyer's checkout page, for the shop to send
    its buyer to."""
    base = config.public_base_url or request.url_root.rstrip('/')

    if not config.is_dev and base.startswith('http://'):
        base = 'https://' + base[len('http://'):]
    return base + url_for('charge.page', charge_code=charge_code)


def _charge_view(charge, merchant, include_payment_details):
    """What a buyer is shown. Never the shop's keys or other charges."""
    view = {
        'charge_code': charge.charge_code,
        'reference': charge.reference,
        'amount': f'{charge.amount:.2f}',
        'currency': charge.currency_ticker.upper(),
        'status': charge.status,
        'method': charge.method,
        'business_name': merchant.business_name,
        'expires_at': charge.expires_at.isoformat(),
        # Drives the countdown on the checkout screen.
        'seconds_remaining': charge.seconds_remaining(),
    }

    if include_payment_details:
        bank_account = checkout.merchant_bank_account(merchant)
        view['bank_transfer'] = {
            'available': bank_account is not None,
            'account_number':
                bank_account.account_number if bank_account else None,
            'bank_name':
                bank_account.account_bank_name if bank_account else None,
            'account_name': merchant.business_name,
            # Said plainly, because a shop whose owner has not finished KYC
            # has no account to be paid into and the buyer must not be left
            # staring at a blank field.
            'unavailable_reason': None if bank_account else
                'this shop cannot accept bank transfers yet',
        }
        view['return_url'] = checkout.return_url(charge)
        view['wallet'] = {
            'available': True,
            'description': 'pay instantly from your Payverve balance',
        }

    return view


class ChargeResource(Resource):
    """ One intended payment to a merchant """

    @staticmethod
    def create(merchant=None):
        """Shop server creates a charge. Idempotent on its own reference."""
        try:
            payload = request.get_json(silent=True) or {}
            charge = checkout.stage_charge(
                merchant,
                reference=payload.get('reference'),
                amount=payload.get('amount'),
                callback_url=payload.get('callback_url'),
                currency_ticker=payload.get('currency', 'ngn'),
            )
            db.session.commit()

            return jsonify({
                'code': 201,
                'status_message': 'created',
                'data': {
                    **_charge_view(charge, merchant, False),
                    # Send the buyer here. The JSON behind it stays at
                    # /checkout/<charge_code>.
                    'checkout_url': checkout_page_url(charge.charge_code),
                }
            }), 201

        except RegistrationError as e:
            db.session.rollback()
            return jsonify(e.as_payload()), e.code

        except (IntegrityError, DataError):
            db.session.rollback()
            return jsonify({
                'code': 400,
                'status_message': 'bad request',
                'message': 'ensure input data are correct'
            }), 400

        except DATABASE_ERRORS:
            db.session.rollback()
            return jsonify({
                'code': 500,
                'status_message': 'database error',
                'message': 'could not create the charge'
            }), 500

    @staticmethod
    def verify(reference=None, merchant=None):
        """Shop server asks whether its own reference is paid.

        This is the only answer a shop should act on. The buyer being
        redirected back proves nothing: that redirect is under their control.
        """
        try:
            charge = ChargeModel.query.filter_by(
                merchant_id=merchant.id, reference=reference).first()

            if not charge:
                return jsonify({
                    'code': 404,
                    'status_message': 'not found',
                    'message': 'no charge with that reference'
                }), 404

            checkout.expire_if_due(charge)
            db.session.commit()

            return jsonify({
                'code': 200,
                'status_message': 'success',
                'data': {
                    **_charge_view(charge, merchant, False),
                    'paid': charge.status == 'paid',
                    'paid_at': charge.paid_at.isoformat()
                    if charge.paid_at else None,
                    'settlement_reference': charge.settlement_reference,
                }
            }), 200

        except DATABASE_ERRORS:
            db.session.rollback()
            return jsonify({
                'code': 500,
                'status_message': 'database error',
                'message': 'could not fetch the charge'
            }), 500


class CheckoutResource(Resource):
    """ What a buyer sees and does """

    @staticmethod
    def read(charge_code=None):
        """What to pay, to whom, how, and how long is left. No session needed."""
        try:
            charge = ChargeModel.query.filter_by(
                charge_code=charge_code).first()

            if not charge:
                return jsonify({
                    'code': 404,
                    'status_message': 'not found',
                    'message': 'this checkout link is not valid'
                }), 404

            merchant = MerchantModel.query.filter_by(
                id=charge.merchant_id).first()

            checkout.expire_if_due(charge)
            db.session.commit()

            return jsonify({
                'code': 200,
                'status_message': 'success',
                'data': _charge_view(charge, merchant, True)
            }), 200

        except DATABASE_ERRORS:
            db.session.rollback()
            return jsonify({
                'code': 500,
                'status_message': 'database error',
                'message': 'could not load the checkout'
            }), 500

    @staticmethod
    def page(charge_code=None):
        """The checkout page a shop sends its buyer to.

        Rendered with everything the buyer needs already in it, so it works
        before any script runs; the script only counts down and polls the JSON
        route for the moment the transfer lands.
        """
        try:
            charge = ChargeModel.query.filter_by(
                charge_code=charge_code).first()
            merchant = MerchantModel.query.filter_by(
                id=charge.merchant_id).first() if charge else None

            if charge:
                checkout.expire_if_due(charge)
                db.session.commit()

            view = _charge_view(charge, merchant, True) if charge else None
            html = render_template(
                'checkout/pay.html', charge=view, failed=False,
                status_url=url_for('charge.read', charge_code=charge_code)
                if charge else None)
            response = make_response(html, 200 if charge else 404)

        except DATABASE_ERRORS:
            db.session.rollback()
            response = make_response(render_template(
                'checkout/pay.html', charge=None, status_url=None,
                failed=True), 500)

        # The page carries a live account number and a countdown: never
        # serve a cached copy, and never leak the code in a Referer.
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Referrer-Policy'] = 'no-referrer'
        return response

    @staticmethod
    def pay_with_wallet(charge_code=None):
        """Buyer settles the charge from their Payverve balance."""
        try:
            buyer_id = request.current_user['sub']
            buyer = UserModel.query.filter_by(id=buyer_id).first()

            if not buyer:
                return jsonify({
                    'code': 404,
                    'status_message': 'not found',
                    'message': 'no user account was found'
                }), 404

            charge = ChargeModel.query.filter_by(
                charge_code=charge_code).first()

            if not charge:
                return jsonify({
                    'code': 404,
                    'status_message': 'not found',
                    'message': 'this checkout link is not valid'
                }), 404

            payload = request.get_json(silent=True) or {}

            # One transaction: the debit, the credit and the charge becoming
            # paid land together or not at all.
            checkout.pay_charge_from_wallet(
                charge, buyer, payload.get('transaction_pin'))

            merchant = MerchantModel.query.filter_by(
                id=charge.merchant_id).first()

            # Queued inside the payment transaction so a paid charge always
            # has its notification on record; sent after the commit, off the
            # request, so a slow shop server never holds the buyer's response.
            delivery = merchant_webhook.enqueue_charge_paid(charge, merchant)
            db.session.commit()

            if delivery:
                run_detached('charge-paid-webhook', _deliver_in_app_context,
                             current_app._get_current_object(), delivery.id)

            return jsonify({
                'code': 200,
                'status_message': 'success',
                'message': 'payment successful',
                'data': {
                    **_charge_view(charge, merchant, False),
                    'paid': True,
                    'settlement_reference': charge.settlement_reference,
                    'callback_url': charge.callback_url,
                }
            }), 200

        except RegistrationError as e:
            db.session.rollback()
            return jsonify(e.as_payload()), e.code

        except (IntegrityError, DataError):
            db.session.rollback()
            return jsonify({
                'code': 400,
                'status_message': 'bad request',
                'message': 'ensure input data are correct'
            }), 400

        except DATABASE_ERRORS:
            db.session.rollback()
            return jsonify({
                'code': 500,
                'status_message': 'database error',
                'message': 'the payment could not be completed'
            }), 500
