"""
src/value_object/password.py
this module defines the PasswordValidation class, which is used to validate passwords.
"""
import re


class PasswordValidation:
    """ PasswordValidation class validates the strength and length of a password. """

    def __init__(self, password: str):
        """ initializes the PasswordValidation with a password."""

        if not self.password_length(password):
            raise ValueError("Password must be at least 8 characters long")

        if not self.password_strength(password):
            raise ValueError(
                "Password must contain at least one uppercase letter, one lowercase letter, one digit, and one special character")

        self.password = password

    @staticmethod
    def password_length(password: str) -> bool:
        """ password_length checks if the password is at least 8 characters long."""

        return len(password) >= 8

    @staticmethod
    def password_strength(password: str) -> bool:
        """ password_strength checks if the password contains at least one uppercase letter, one lowercase letter, one digit, and one special character."""

        password_regex = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[\W_]).{8,}$'

        return re.match(password_regex, password) is not None
