"""

"""


class NINCheck:
    """  """

    def __init__(self, nin: str):
        if not self.nin_length(nin):
            raise ValueError("NIN must be exactly 11 digit.")

        self._nin = nin

    @staticmethod
    def nin_length(nin: str) -> bool:
        """ """

        nin_length = len(nin) == 11

        return nin_length
