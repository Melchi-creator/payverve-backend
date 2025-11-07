"""
src/value_object/min_balance.py
This module defines the MinimumBalance class, which is used to validate minimum balance values.
It ensures that the value is a positive number.
"""


class MinimumBalance:
    """ MinimumBalance class validates that the balance is a positive number. """

    def __init__(self, value: float):
        if not self.minimum_value(value):
            raise ValueError("Balance cannot be less than zero, must be a positive number.")

        self._value = value

    @staticmethod
    def minimum_value(value: float) -> bool:
        """ minimum_value checks if the value is a positive number."""

        min_value = value >= 0

        return min_value
