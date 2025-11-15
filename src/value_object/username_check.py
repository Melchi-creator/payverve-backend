"""

"""

import re


class UsernameCheck:
    """ """

    def __init__(self, username: str):
        if not self.is_valid_username(username):
            raise ValueError(f"Invalid username: {username} - must be 4-10 lowercase alphanumeric characters.")
        self.username = username

    @staticmethod
    def is_valid_username(username) -> bool:
        """ Check if the username address is valid."""

        return bool(re.match(r"^[a-z0-9]{4,10}$", username))