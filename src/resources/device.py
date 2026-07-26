"""
src/resources/device.py
Handles device-specific data, such as FCM tokens used for push notifications.
"""

from flask import jsonify, request
from flask_restful import Resource
from flask_restful.reqparse import Argument
from sqlalchemy.exc import DBAPIError, DisconnectionError
from psycopg2 import InternalError, OperationalError, ProgrammingError

from src.models import UserModel
from src.utilities import parse_params


class DeviceResource(Resource):
    """ """

    @staticmethod
    @parse_params(
        Argument("fcm_token", location="json", required=True),
    )
    def register_fcm_token(fcm_token: str):
        """
        Registers or updates the FCM token for the currently authenticated user's device.
        Called by the Flutter app after login and whenever the token refreshes.
        """
        try:
            user_id = request.current_user['sub']

            user = UserModel.query.filter_by(id=user_id).first()

            if not user:
                return jsonify({
                    'code': 404,
                    'status_message': 'not found',
                    'message': 'user not found'
                }), 404

            user.fcm_token = fcm_token
            user.save()

            return jsonify({
                'code': 200,
                'status_message': 'successful',
                'message': 'device token registered successfully'
            })

        except (ProgrammingError, DBAPIError, DisconnectionError, InternalError, OperationalError):
            return jsonify({
                "code": 500,
                'status_message': 'database error',
                'message': "this error is a database error",
            }), 500
