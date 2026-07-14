from server import server
from src.models import CurrencyModel, KYCModel

with server.app_context():
    print("=== Currencies ===")
    for c in CurrencyModel.query.all():
        print(c.id, c.short_code)

    print("=== KYC ===")
    k = KYCModel.query.filter_by(
        user_id='46f95cf1-0a75-49ec-ada8-307ac3f63595').first()
    print(k.tier if k else 'NO KYC RECORD')
