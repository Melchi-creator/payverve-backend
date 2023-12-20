from enum import Enum


class TransactionStatus(Enum):
    INITIATED = 'Initiated'
    PENDING = 'Pending'
    COMPLETED = 'Completed'

    @classmethod
    def choices(cls):
        return [(item.value, item.name) for item in cls]
