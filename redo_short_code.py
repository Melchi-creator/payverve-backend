from server import server
from src.models import VirtualAccountNumberModel, db

with server.app_context():
    rows = VirtualAccountNumberModel.query.filter_by(
        user_id='65db9d88-df0d-4585-82cf-82e53e586fe1').all()
    for r in rows:
        print("Deleting:", r.id, r.account_number, r.currency_ticker)
        db.session.delete(r)
    db.session.commit()
    print("Cleaned up.")
