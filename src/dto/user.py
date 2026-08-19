"""

"""
import re
from typing import Annotated

from pydantic import AfterValidator, EmailStr, StringConstraints

from .dto_config import StrictBaseModel


class UserDTOCreate(StrictBaseModel):
    """Data transfer object for creating a new user."""

    @staticmethod
    def password_validator(password: str) -> str:
        """Validates the strength of the password."""

        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")

        checker = re.match(
            r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$",
            password,
        )

        if not checker:
            raise ValueError(
                "Password must contain at least one uppercase letter, one lowercase letter, one digit, and one special character"
            )

        return password

    first_name: Annotated[str, StringConstraints(strip_whitespace=True, strict=True, min_length=1), 'First name of the user.']
    last_name: Annotated[str, StringConstraints(strip_whitespace=True, strict=True, min_length=1), 'Last name of the user.']
    username: Annotated[str, StringConstraints(strip_whitespace=True, strict=True, min_length=1), 'Username for the user account.']
    email_address: Annotated[EmailStr, StringConstraints(strip_whitespace=True, strict=True, pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'), 'Email address of the user.']
    mobile_number: Annotated[ str, StringConstraints(strip_whitespace=True,strict=True, min_length=10, max_length=15), 'Mobile number of the user.']
    password: Annotated[str, StringConstraints(strip_whitespace=True, strict=True, min_length=8), AfterValidator(password_validator), 'Password for the user account.']
    referral_code: Annotated[str, StringConstraints(strip_whitespace=True, strict=True, min_length=0), 'Referral code for the user account.'] = None
    gender: Annotated[str, StringConstraints(strip_whitespace=True, strict=True, min_length=1), 'Gender of the user.']
    date_of_birth: Annotated[str, StringConstraints(strip_whitespace=True, strict=True, min_length=1), 'Date of birth of the user.']
    # Optional at signup. BellBank issues a virtual account against a
    # verified identity, so sending both provisions a real account number
    # during registration; omitting them leaves the wallet unprovisioned
    # until KYC supplies them. extra='forbid' means the model has to name
    # them or the request is rejected outright.
    bvn: Annotated[str, StringConstraints(strip_whitespace=True, strict=True, min_length=11, max_length=11), 'Bank verification number.'] = None
    address: Annotated[str, StringConstraints(strip_whitespace=True, strict=True, min_length=1), 'Residential address.'] = None
