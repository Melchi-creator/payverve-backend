"""

"""

from flask import Blueprint

from ..auth import jwt_required
from ..resources import NotificationResource

NotificationBlueprint = Blueprint("notification", __name__)

NotificationBlueprint.route("/notifications/<uuid:id>", methods=['GET'])(jwt_required(NotificationResource.read_user_message))
NotificationBlueprint.route("/notifications/mark-as-read/<uuid:id>", methods=['GET'])(jwt_required(NotificationResource.mark_as_read))
NotificationBlueprint.route("/notifications/mark-all-as-read/<uuid:id>", methods=['GET'])(jwt_required(NotificationResource.mark_all_as_read))
NotificationBlueprint.route("/notifications/count-read/<uuid:id>", methods=['GET'])(jwt_required(NotificationResource.count_read_message))
NotificationBlueprint.route("/notifications/count-unread/<uuid:id>", methods=['GET'])(jwt_required(NotificationResource.count_unread_message))
