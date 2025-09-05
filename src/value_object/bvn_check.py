"""

"""


class BVNCheck:
    """  """

    def __init__(self, bvn: str):
        if not self.bvn_length(bvn):
            raise ValueError("BVN must be exactly 11 digit.")

        self._bvn = bvn

    @staticmethod
    def bvn_length(bvn: str) -> bool:
        """ """

        bvn_length = len(bvn) == 11

        return bvn_length
