from server import server
from src.models import KYCModel, db

with server.app_context():
    k = KYCModel.query.filter_by(
        user_id='65db9d88-df0d-4585-82cf-82e53e586fe1').first()
    k.tier = 3
    k.bvn = '12345678901'
    k.address = '123 Test Street, Lagos, Nigeria'
    db.session.commit()
    print("Updated:", k.tier, k.bvn, k.address)
