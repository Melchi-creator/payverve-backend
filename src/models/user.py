"""
user.py

Defines the model structure for users
"""
from uuid import uuid4

from flask_login import UserMixin
from sqlalchemy import UUID
from werkzeug.security import check_password_hash, generate_password_hash

from ..middlewares import NetworkDateTime
from . import db
from .abc import BaseModel, MetaBaseModel


class UserModel(db.Model, BaseModel, UserMixin, metaclass=MetaBaseModel):
    """ User Model """

    __tablename__ = 'users'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    first_name = db.Column(db.String(), nullable=False)
    last_name = db.Column(db.String(), nullable=False)
    middle_name = db.Column(db.String(), nullable=True)
    username = db.Column(db.String(), nullable=True)
    email_address = db.Column(db.String(), nullable=False, unique=True)
    mobile_number = db.Column(db.String(), nullable=False, unique=True)
    password = db.Column(db.String(), nullable=False)
    auth_pin = db.Column(db.String(), nullable=True)
    transaction_pin = db.Column(db.String(), nullable=True)
    gender = db.Column(db.String(), nullable=False)
    date_of_birth = db.Column(db.Date(), nullable=False)
    house_number = db.Column(db.String(), nullable=True)
    street_name = db.Column(db.String(), nullable=True)
    city = db.Column(db.String(), nullable=True)
    state = db.Column(db.String(), nullable=True)
    zipcode = db.Column(db.Integer, nullable=True)
    country = db.Column(db.String(), nullable=True)
    photo = db.Column(db.String(), nullable=True)
    deleted = db.Column(db.Boolean(), nullable=False, default=False)
    deleted_date = db.Column(db.DateTime(), nullable=True)

    created_at = db.Column(db.DateTime(), default=NetworkDateTime.network_datetime(), nullable=False)
    updated_at = db.Column(db.DateTime(), onupdate=NetworkDateTime.network_datetime(), nullable=True)

    # relationships

    bank_accounts = db.relationship('BankAccountModel', backref='users', lazy=True, cascade="all")
    beneficiaries = db.relationship('BeneficiaryModel', backref='users', lazy=True, cascade="all")
    foreign_transfers = db.relationship('ForeignTransferModel', backref='users', lazy=True, cascade="all")
    local_transfers = db.relationship('LocalTransferModel', backref='users', lazy=True, cascade="all")
    swapped_currencies = db.relationship('SwapCurrencyModel', backref='users', lazy=True, cascade="all")
    payverve_transfers = db.relationship('PayverveTransferModel', backref='users', lazy=True, cascade="all")
    wallets = db.relationship('WalletModel', backref='users', lazy=True, cascade="all")

    def set_password(self, password):
        """ hashes user password """

        self.password = generate_password_hash(password)

    def check_password(self, password):
        """ verify hashed user password """

        return check_password_hash(self.password, password)

    def set_auth_pin(self, auth_pin):
        """ hashes user transaction pin """

        self.password = generate_password_hash(auth_pin)

    def check_auth_pin(self, auth_pin):
        """ verify hashed user transaction pin """

        return check_password_hash(self.auth_pin, auth_pin)

    def set_transaction_pin(self, transaction_pin):
        """ hashes user transaction pin """

        self.password = generate_password_hash(transaction_pin)

    def check_transaction_pin(self, transaction_pin):
        """ verify hashed user transaction pin """

        return check_password_hash(self.transaction_pin, transaction_pin)
