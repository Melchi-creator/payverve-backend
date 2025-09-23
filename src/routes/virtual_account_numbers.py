"""

"""

from flask import Blueprint

from ..auth import jwt_required
from ..resources import VirtualAccountNumberResource

VirtualAccountNumberBlueprint = Blueprint("virtual_account_number", __name__)

VirtualAccountNumberBlueprint.route("/virtual-account-numbers",
                                    methods=['GET'])(jwt_required(VirtualAccountNumberResource.read_all))
VirtualAccountNumberBlueprint.route("/virtual-account-numbers/<uuid:id>",
                                    methods=['GET'])(jwt_required(VirtualAccountNumberResource.read_one))
VirtualAccountNumberBlueprint.route("/virtual-account-numbers/user/<uuid:id>",
                                    methods=['GET'])(jwt_required(VirtualAccountNumberResource.user_virtual_account))
