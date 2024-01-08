from rave_python import Rave, RaveExceptions, Misc
from django.conf import settings

rave = Rave(publicKey=settings.FLUTTERWAVE_PUBLIC_KEY, production=settings.PRODUCTION,
            secretKey=settings.FLUTTERWAVE_SECRET_KEY)

payload_sample_account = {
    "amount": 123,
    "currency": "GBP",
    "email": "",
    "firstname": "",
    "lastname": "",
    "ip": "",  # optional
    "redirectUrl": "",  # optional
    "PBFPubKey": settings.FLUTTERWAVE_PUBLIC_KEY
}

payload_sample_card = {
    "cardno": "5438898014560229",
    "cvv": "890",
    "expirymonth": "09",
    "expiryyear": "19",
    "amount": "10",
    "email": "user@gmail.com",
    "phonenumber": "0902620185",
    "firstname": "temi",
    "lastname": "desola",
    "IP": "355426087298442",
}

"""This is used to facilitate account transactions. 
Transactions initiated via this method are authorized by the user on their Banking platform."""


class Account:

    def charge(self, payload):
        try:
            res = rave.Account.charge(payload)
            if res["authUrl"]:
                print(res["authUrl"])

            elif res["validationRequired"]:
                rave.Account.validate(res["flwRef"], "12345")

            res = rave.Account.verify(res["txRef"])
            # print(res)
            return res

        except RaveExceptions.AccountChargeError as e:
            print(e.err)
            print(e.err["flwRef"])

        except RaveExceptions.TransactionValidationError as e:
            print(e.err)
            print(e.err["flwRef"])

        except RaveExceptions.TransactionVerificationError as e:
            print(e.err["errMsg"])
            print(e.err["txRef"])

    def verify(self, txRef):
        """"""
        res = rave.Account.verify(txRef)
        return res


class Card:

    def charge(self, payload):
        """
        This is called to start a card transaction. The payload should be a dictionary containing card information.
        @param payload:
        """
        try:
            res = rave.Card.charge(payload)

            if res["suggestedAuth"]:
                arg = Misc.getTypeOfArgsRequired(res["suggestedAuth"])

                if arg == "pin":
                    Misc.updatePayload(res["suggestedAuth"], payload, pin="3310")
                if arg == "address":
                    Misc.updatePayload(res["suggestedAuth"], payload,
                                       address={"billingzip": "07205", "billingcity": "Hillside",
                                                "billingaddress": "470 Mundet PI", "billingstate": "NJ",
                                                "billingcountry": "US"})

                res = rave.Card.charge(payload)

            if res["validationRequired"]:
                rave.Card.validate(res["flwRef"], "")

            res = rave.Card.verify(res["txRef"])
            print(res["transactionComplete"])

        except RaveExceptions.CardChargeError as e:
            print(e.err["errMsg"])
            print(e.err["flwRef"])

        except RaveExceptions.TransactionValidationError as e:
            print(e.err)
            print(e.err["flwRef"])

        except RaveExceptions.TransactionVerificationError as e:
            print(e.err["errMsg"])
            print(e.err["txRef"])

    def refund(self):
        pass

    def validate(self, txRef):
        pass

    def verify(self, txRef):
        pass

    def get_type_of_args_required(self):
        pass

    def update_payload(self,authMethod, payload, arg):
        pass

    def charge(self,payload_for_saved_card, chargeWithToken=True):
        pass