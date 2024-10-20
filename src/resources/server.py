"""
server.py
This file verifies the server is running and accessbile
"""

from flask import jsonify
from flask_restful import Resource


class Server(Resource):
    """
    Defines functions to test server activeness
    """

    @staticmethod
    def server():
        """
        This funtion confirms that the server is running
        """

        return jsonify({
            'code': 200,
            'code_message': 'success',
            'data': 'The server is running!'
        })
