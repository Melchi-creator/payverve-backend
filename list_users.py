from server import server
from src.models import UserModel, KYCModel, WalletModel, CurrencyModel

with server.app_context():
    users = UserModel.query.all()
    for u in users:
        kyc = KYCModel.query.filter_by(user_id=u.id).first()
        print(f"id={u.id} | email={u.email_address} | mobile={u.mobile_number} | kyc_tier={kyc.tier if kyc else 'NO KYC'}")
