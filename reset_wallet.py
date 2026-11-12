from server import server
from src.models import WalletModel, db

with server.app_context():
    w = WalletModel.query.filter_by(
        user_id='46f95cf1-0a75-49ec-ada8-307ac3f63595',
        currency_id='b82c9f7e-e210-4603-a83f-057f27fb579d'
    ).first()
    w.is_active = False
    w.account_number = None
    w.bank_name = None
    w.external_reference = None
    w.flutterwave_account_id = None
    db.session.commit()
    print("Wallet reset for re-test")
