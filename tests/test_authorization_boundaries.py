"""Endpoints that expose customer data must not be reachable anonymously.

jwt_required is the only auth decorator in this codebase, and it checks neither
role nor ownership. Several routes did not even have it:

  GET  /token-verifications  returned code_sent and the channel_contact it went
                             to for every token, newest first -- a password
                             reset for any address, then read the OTP here, then
                             reset the password. No account needed.
  POST /admins               with zero admin rows, anyone could mint the first
  POST /admin-roles          admin and inherit platform-wide read access.
  GET  /payverve-wallets     Payverve's own float, decrypted.
  GET  /beneficiaries        every saved payee on the platform.

And POST /local-transfers authorised on a user_id taken from the request body,
checking only that wallet_id belonged to it -- both caller-supplied and
self-consistent -- while GET /wallets handed out every wallet id, user_id and
decrypted balance. Those two together drained any wallet to any bank account.

Run:  ENV=development PYTHONPATH=. python tests/test_authorization_boundaries.py
"""
import sys

import src.resources  # noqa: F401  (import order: resources before middlewares)
import server

_failures = []


def check(label, got, want):
    ok = got == want
    if not ok:
        _failures.append(label)
    print(f"{'PASS' if ok else 'FAIL'}  {label:<56} got={got!r} want={want!r}")


# Reachable without a token means reachable by the whole internet.
MUST_REQUIRE_AUTH = [
    ('GET', '/token-verifications'),
    ('POST', '/admins'),
    ('GET', '/admins'),
    ('PUT', '/admins/9b16338e-57dc-414b-b835-50cd11d9874b'),
    ('DELETE', '/admins/9b16338e-57dc-414b-b835-50cd11d9874b'),
    ('POST', '/admin-roles'),
    ('GET', '/admin-roles'),
    ('GET', '/payverve-wallets'),
    ('GET', '/beneficiaries'),
    ('POST', '/beneficiaries'),
    ('GET', '/beneficiaries/9b16338e-57dc-414b-b835-50cd11d9874b'),
    ('PUT', '/beneficiaries/9b16338e-57dc-414b-b835-50cd11d9874b'),
    ('DELETE', '/beneficiaries/9b16338e-57dc-414b-b835-50cd11d9874b'),
]

# Deliberately public: anonymous callers have to be able to reach these.
MUST_STAY_PUBLIC = [
    ('GET', '/'),
    ('POST', '/user-login'),
    ('POST', '/users'),
    ('POST', '/users/verify'),
    ('POST', '/users/request-password-reset'),
    # /bellbank/webhook is deliberately absent. It carries no jwt_required,
    # but it fails closed with 401 when neither BELLBANK_WEBHOOK_SECRET nor
    # BELLBANK_WEBHOOK_IPS is set, so a status probe cannot tell "no JWT
    # needed" from "rejected". test_webhook_auth covers it properly.
]


def main():
    app = server.server

    with app.test_client() as client:
        for method, path in MUST_REQUIRE_AUTH:
            code = client.open(path, method=method, json={}).status_code
            check(f'{method} {path} rejects anonymous', code, 401)

        print()

        for method, path in MUST_STAY_PUBLIC:
            code = client.open(path, method=method, json={}).status_code
            # Anything but 401 -- these may well 400 or 404 on an empty body,
            # but they must not demand a token.
            check(f'{method} {path} stays public', code != 401, True)

    print()

    # The OTP itself must not be in the response shape at all, for any caller.
    from src.resources.token_verification import TokenVerification
    import inspect
    body = inspect.getsource(TokenVerification.read)
    check('token-verifications never emits code_sent',
          "'code_sent':" in body, False)

    # local_transfer must consult the token, not just the body.
    from src.resources import local_transfer as lt
    create_src = inspect.getsource(lt.LocalTransferResource.create)
    check('local-transfers authorises against the token',
          'owns(user_id)' in create_src, True)

    # wallets read_all must not be an unscoped dump.
    from src.resources import wallet as w
    read_all_src = inspect.getsource(w.WalletResource.read_all)
    check('wallets read_all is scoped to the caller',
          'caller_id()' in read_all_src, True)

    # Withdrawals, pin control and savings mutation all keyed the owner off
    # the URL. Each must now establish the caller from the token.
    OWNERSHIP_GUARDED = [
        ('src.resources.user', 'UserResource', 'user_create_transaction_pin', 'id'),
        ('src.resources.user', 'UserResource', 'user_change_transaction_pin', 'id'),
        ('src.resources.user', 'UserResource', 'confirm_transaction_pin', 'id'),
        ('src.resources.user', 'UserResource', 'user_create_auth_pin', 'id'),
        ('src.resources.user', 'UserResource', 'user_change_auth_pin', 'id'),
        ('src.resources.user', 'UserResource', 'confirm_auth_pin', 'id'),
        ('src.resources.spend_save', 'SpendSaveResource', 'withdraw_spend_save', 'id'),
        ('src.resources.spend_save', 'SpendSaveResource', 'update_percentage', 'id'),
        ('src.resources.spend_save', 'SpendSaveResource', 'toggle_spend_save', 'id'),
        ('src.resources.spend_save', 'SpendSaveResource', 'user_read', 'id'),
        ('src.resources.target_save', 'TargetSaveResource', 'withdraw_target_saving', 'user_id'),
        ('src.resources.target_save', 'TargetSaveResource', 'break_ts', 'user_id'),
        ('src.resources.target_save', 'TargetSaveResource', 'delete_target_saving', 'user_id'),
        ('src.resources.target_save', 'TargetSaveResource', 'fetch_user_ts', 'id'),
        ('src.resources.fixed_deposit', 'FixedDepositResource', 'withdraw_fixed_deposit', 'user_id'),
        ('src.resources.fixed_deposit', 'FixedDepositResource', 'fetch_user_fd', 'id'),
    ]

    import importlib

    for module_name, cls_name, fn_name, owner in OWNERSHIP_GUARDED:
        module = importlib.import_module(module_name)
        fn = getattr(getattr(module, cls_name), fn_name)
        body = inspect.getsource(fn)
        check(f'{fn_name} checks owns({owner})',
              f'owns({owner})' in body, True)

    print()
    if _failures:
        print(f'{len(_failures)} FAILED: ' + ', '.join(_failures))
        return 1
    print('ALL PASS')
    return 0


if __name__ == '__main__':
    sys.exit(main())
