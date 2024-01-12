# Create your models here.
class Wallet:
    # balance, userId, timestamps
    pass


class WalletTransaction:
    # amount, userId, isInflow, paymentMethod, currency, status, timestamps
    pass


class Transaction:
    # userId, transactionId, name, email, phone, amount, currency, paymentStatus, paymentGateway, timestamps
    pass


class User:
    # first_name: {type: String, default: null},
    # last_name: {type: String, default: null},
    # email: {type: String, unique: true},
    # password:
    pass
