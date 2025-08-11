"""
src/value_object/email_address.py
This module defines the EmailCheck class, which represents an email value object.
It validates that the email address contains an '@' symbol to ensure it is a valid email address
"""

import re


class EmailCheck:
    """ this class represents the email value-object in the system."""

    def __init__(self, email_address: str):
        if not self.is_valid_email(email_address):
            raise ValueError(f"Invalid email: {email_address}")
        self.email_address = email_address

    @staticmethod
    def is_valid_email(email_address) -> bool:
        """ Check if the email address is valid."""

        return bool(re.match(r"[^@]+@[^@]+\.[^@]+", email_address))
