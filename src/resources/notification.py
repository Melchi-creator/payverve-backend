"""

"""
from typing import Optional

from flask import jsonify
from flask_restful import Resource

from ..models import NotificationModel


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
                    "created_at": message.created_at,
                    "updated_at": message.updated_at,
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
