from server import server
from src.models import WalletModel

with server.app_context():
    w = WalletModel.query.filter_by(
        user_id='46f95cf1-0a75-49ec-ada8-307ac3f63595',
        currency_id='b82c9f7e-e210-4603-a83f-057f27fb579d'
    ).first()
    print("account_number:", w.account_number)
    print("bank_name:", w.bank_name)
    print("external_reference:", w.external_reference)
    print("flutterwave_account_id:", w.flutterwave_account_id)
    print("is_active:", w.is_active)
