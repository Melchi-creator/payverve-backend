from server import server
from src.models import KYCModel, db

with server.app_context():
    k = KYCModel.query.filter_by(
        user_id='46f95cf1-0a75-49ec-ada8-307ac3f63595').first()
    k.tier = 3
    k.bvn = '12345678901'
    k.address = '123 Test Street, Lagos, Nigeria'
    db.session.commit()
    print("Updated:", k.tier, k.bvn, k.address)
