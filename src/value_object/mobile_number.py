"""

"""

import re


class MobileNumberCheck:
    """ this class represents the mobile number value-object in the system."""

    def __init__(self, mobile_number: str):
        if not self.is_valid_mobile_number(mobile_number):
            raise ValueError(f"Invalid mobile number: {mobile_number}")
        self.mobile_number = mobile_number

    @staticmethod
    def is_valid_mobile_number(mobile_number) -> bool:
        """ Check if the mobile number address is valid."""

        return bool(re.match(r"^(\+?234|0)?\s*[789][01]\s*\d{3}\s*\d{3}\s*\d{2}$", mobile_number))
