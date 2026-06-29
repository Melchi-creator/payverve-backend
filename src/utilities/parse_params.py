"""
Wrap parameters parsing
As it's quite ugly and messy
"""
from functools import wraps

from flask_restful import reqparse


def parse_params(*arguments):
    """
    Parse the parameters
    Forward them to the wrapped function as named parameters
    """

    def parse(func):
        @wraps(func)
        def resource_verb(*args, **kwargs):
            parser = reqparse.RequestParser()
            for argument in arguments:
                parser.add_argument(argument)
            parsed = parser.parse_args()

            kwargs.update(parsed)

            return func(*args, **kwargs)  # ← this line was commented out

        return resource_verb
    return parse
