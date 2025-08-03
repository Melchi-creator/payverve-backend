"""
src/models/user.py
This module defines the UserModel class, which represents a user in the application.
It includes fields for user information, relationships with other models, and methods for password and PIN management
"""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import UUID
from werkzeug.security import check_password_hash, generate_password_hash

from . import db
from .abc import BaseModel, MetaBaseModel



class UserModel(db.Model, BaseModel, metaclass=MetaBaseModel):
    """ UserModel represents a user in the application."""

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
    account_active = db.Column(db.Boolean(), nullable=False, default=False)
    deleted = db.Column(db.Boolean(), nullable=False, default=False)
    deleted_date = db.Column(db.DateTime(), nullable=True)
    email_verified = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime(), default=datetime.now(), nullable=False)
    updated_at = db.Column(db.DateTime(), onupdate=datetime.now(), nullable=True)

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

        self.auth_pin = generate_password_hash(auth_pin)

    def check_auth_pin(self, auth_pin):
        """ verify hashed user transaction pin """

        return check_password_hash(self.auth_pin, auth_pin)

    def set_transaction_pin(self, transaction_pin):
        """ hashes user transaction pin """

        self.transaction_pin = generate_password_hash(transaction_pin)

    def check_transaction_pin(self, transaction_pin):
        """ verify hashed user transaction pin """

        return check_password_hash(self.transaction_pin, transaction_pin)
