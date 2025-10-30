"""
server.py

Resources for server check
"""

from flask.json import jsonify
from flask_restful import Resource


class ServerResource(Resource):
    """ The server confirmation class """

    @staticmethod
    def status_check():
        """ The function to check if the server is running """

        try:
            return jsonify({
                'code': 200,
                'status_message': 'success',
                'message': 'The server is running succuessfully'
            }), 200

        except (ConnectionError, ConnectionRefusedError):
            return jsonify({
                'code': 500,
                'status_message': 'interval server error',
                'message': 'The server is not running, something went wrong'
            }), 500
