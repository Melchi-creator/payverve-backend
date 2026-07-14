from server import server
from src.models import KYCModel

with server.app_context():
    k = KYCModel.query.filter_by(
        user_id='46f95cf1-0a75-49ec-ada8-307ac3f63595').first()
    if k:
        print(vars(k))
    else:
        print("NO KYC RECORD")
