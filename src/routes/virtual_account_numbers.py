"""

"""

from flask import Blueprint

from ..auth import jwt_required
from ..resources import VirtualAccountNumberResource

VirtualAccountNumberBlueprint = Blueprint("virtual_account_number", __name__)

VirtualAccountNumberBlueprint.route("/virtual-account-numbers",
                                    methods=['GET'])(jwt_required(VirtualAccountNumberResource.read_all))
