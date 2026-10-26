"""

"""

from flask import Blueprint

from ..resources.transfer_settlement import TransferSettlementResource

TransferSettlementBlueprint = Blueprint("transfer_settlement", __name__)

# NOT jwt_required: the caller is the scheduled GitHub Action, not a customer.
# It is authenticated by SETTLE_TRANSFERS_SECRET inside the resource, which
# fails closed when the secret is unset.
TransferSettlementBlueprint.route(
    "/internal/settle-transfers",
    methods=['POST'])(TransferSettlementResource.settle_pending)
