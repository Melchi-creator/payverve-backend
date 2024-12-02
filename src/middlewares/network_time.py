"""
network_time.py

Defines a function to fetch internet time
"""
from datetime import datetime, timezone

import ntplib


# OopCompanion:suppressRename


class NetworkDateTime:
    """ Defines functions for internet time date """

    @staticmethod
    def network_datetime():
        """ Fetches datetime from the internet """

        client = ntplib.NTPClient()

        try:
            response = client.request('time.windows.com', version=3)
            network_time = datetime.fromtimestamp(response.tx_time, tz=timezone.utc)
            return network_time

        except ConnectionError:
            response = client.request('time.google.com', version=3)
            network_time = datetime.fromtimestamp(response.tx_time, tz=timezone.utc)
            return network_time

        except (Exception, ntplib.NTPException):
            network_time = datetime.now()
            return network_time
