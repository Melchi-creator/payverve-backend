from server import server
from src.models import UserModel

with server.app_context():
    u = UserModel.query.filter_by(id='65db9d88-df0d-4585-82cf-82e53e586fe1').first()
    print("customer_code:", u.customer_code)