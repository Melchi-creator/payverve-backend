"""

"""
from src.models import CurrencyModel


class DBDefaults:

    @staticmethod
    def currency_defaults():
        """ """

        check_currenies = CurrencyModel.query.all()
        short_codes = [currency.short_code for currency in check_currenies]

        if "ngn" not in short_codes:
            # noinspection  PyArgumentList
            ngn_currency = CurrencyModel(
                name="Nigerian Naira",
                short_code="ngn",
                country="Nigeria",
            )
            ngn_currency.save()

        if "usd" not in short_codes:
            # noinspection  PyArgumentList
            usd_currency = CurrencyModel(
                name="United States Dollar",
                short_code="usd",
                country="United States",
            )
            usd_currency.save()

        if "gbp" not in short_codes:
            # noinspection  PyArgumentList
            gbp_currency = CurrencyModel(
                name="Great Britain Pound",
                short_code="gbp",
                country="United Kingdom",
            )
            gbp_currency.save()

        if "ghs" not in short_codes:
            # noinspection  PyArgumentList
            ghs_currency = CurrencyModel(
                name="Ghana Cedi",
                short_code="ghs",
                country="Ghana",
            )
            ghs_currency.save()
