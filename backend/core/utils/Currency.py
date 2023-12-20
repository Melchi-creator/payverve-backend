from enum import Enum


class Currency(Enum):
    Pound = '£'
    Dollar = '$'
    Naira = 'NGN'

    @classmethod
    def choices(cls):
        return [(item.value, item.name) for item in cls]

#
# def choices(cls):
#     return [(item.value, item.name) for item in cls]
