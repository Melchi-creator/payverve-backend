"""

"""
from typing import Optional

from flask import jsonify
from flask_restful import Resource

from ..models import NotificationModel, UserModel
from ..utilities.push_notifications import send_push_notification


class NotificationResource(Resource):
    """ """

    @staticmethod
    def store_nofication(title: str, body: str, user_id=None, topic: Optional[str] = None, admin_id=None):
        """ Store a message in the database for later retrieval."""

        try:

            # noinspection PyArgumentList
            store_message = NotificationModel(
                title=title,
                body=body,
                user_id=user_id,
                admin_id=admin_id,
                topic=topic,
            )

            response = store_message.save()

            return response

        except Exception as e:
            return {"message": str(e)}, 500

    @staticmethod
    def store_and_push(title: str, body: str, user_id=None, data: Optional[dict] = None):
        """ Store a message AND push it to the user's device.

        Money movement has to reach the user when the app is closed, so these
        events need both halves: the row backs the in-app notification list,
        the push is what actually alerts them. store_nofication only ever wrote
        the row, which is why deposits and withdrawals were silent on device
        while the in-app list filled up correctly.

        A push failure never propagates -- by the time this runs the money has
        already moved, and a Firebase outage must not roll that back.
        """

        response = NotificationResource.store_nofication(
            title=title, body=body, user_id=user_id)

        try:
            user = UserModel.query.filter_by(id=user_id).first()

            if not user:
                print(f'[notification] no user {user_id}, push skipped')
                return response

            if not user.fcm_token:
                # Expected for a user who has not signed in since the app
                # started registering tokens, or who denied notifications.
                print(f'[notification] user {user_id} has no fcm token, push skipped')
                return response

            # FCM rejects a data payload whose values are not all strings.
            payload = {k: str(v) for k, v in (data or {}).items()}

            send_push_notification(
                fcm_token=user.fcm_token,
                title=title,
                body=body,
                data=payload,
            )

        except Exception as e:
            print(f'[notification] push failed for user {user_id}: {e}')

        return response

    @staticmethod
    def read_user_message(id=None):
        """ this function will read all messages for a specific user"""

        try:

            messages = NotificationModel.query.filter_by(user_id=id).order_by(NotificationModel.created_at.desc()).all()

            if not messages:
                return jsonify({
                    "code": 404,
                    "code_message": "Not Found",
                    "data": "No messages found for this user"
                }), 404

            data = [
                {
                    "id": message.id,
                    "title": message.title,
                    "body": message.body,
                    "user_id": message.user_id,
                    "topic": message.topic,
                    "is_read": message.is_read,
                    'created_at': message.created_at.strftime("%d %b %Y, %I:%M %p"),
                    'updated_at': message.updated_at.strftime("%d %b %Y, %I:%M %p") if message.updated_at else None,
                }
                for message in messages
            ]

            return jsonify({
                'code': 200,
                'code_message': 'successful',
                'data': data
            }), 200

        except Exception as e:
            return jsonify({
                "code": 500,
                "code_message": "Internal Server Error",
                "data": f"Failed to read messages: {str(e)}",
            }), 500

    @staticmethod
    def mark_as_read(id=None):
        """ """

        try:

            notification = NotificationModel.query.filter_by(id=id).first()

            if not notification:
                return jsonify({
                    "code": 404,
                    "code_message": "Not Found",
                    "data": "No messages found for this user"
                }), 404

            notification.is_read = True
            notification.save()

            return jsonify({
                'code': 200,
                'code_message': 'successful',
                'data': 'message has been marked as read'
            }), 200

        except Exception as e:
            return jsonify({
                "code": 500,
                "code_message": "Internal Server Error",
                "data": f"Failed to update message: {str(e)}",
            }), 500

    @staticmethod
    def mark_all_as_read(id=None):
        """ """

        try:

            notification = NotificationModel.query.filter_by(user_id=id, is_read=False).all()

            if not notification:
                return jsonify({
                    "code": 404,
                    "code_message": "Not Found",
                    "data": "No messages found for this user"
                }), 404

            for notification in notification:
                notification.is_read = True
                notification.save()

            return jsonify({
                'code': 200,
                'code_message': 'successful',
                'data': 'all messages has been marked as read'
            }), 200

        except Exception as e:
            return jsonify({
                "code": 500,
                "code_message": "Internal Server Error",
                "data": f"Failed to update message: {str(e)}",
            }), 500

    @staticmethod
    def count_read_message(id=None):
        """ this function will count all read messages for a specific user"""

        try:
            count = NotificationModel.query.filter_by(user_id=id, is_read=True).count() or 0

            return jsonify({
                'code': 200,
                'code_message': 'successful',
                'data': count
            }), 200

        except Exception as e:
            return jsonify({
                "code": 500,
                "code_message": "Internal Server Error",
                "data": f"Failed to count messages: {str(e)}",
            }), 500

    @staticmethod
    def count_unread_message(id=None):
        """ the function will count all unread messages for a specific user"""

        try:
            count = NotificationModel.query.filter_by(user_id=id, is_read=False).count() or 0

            return jsonify({
                'code': 200,
                'code_message': 'successful',
                'data': count
            }), 200

        except Exception as e:
            return jsonify({
                "code": 500,
                "code_message": "Internal Server Error",
                "data": f"Failed to count messages: {str(e)}",
            }), 500
