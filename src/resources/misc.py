"""

"""
from hmac import compare_digest

from flask import jsonify
from flask_restful import Resource

from ..middlewares import FlutterwaveHelper


class MiscellaneousResources(Resource):
    """ """

    @staticmethod
    def list_ngn_banks():
        """ """

        try:

            response = FlutterwaveHelper.flutterwave_list_of_banks('NG')

            if not compare_digest(str(response.status_code), '200'):
                return jsonify({
                    'code': response.status_code,
                    'status_message': 'failed to fetch banks',
                    'message': response.json().get('message', 'an error occurred while fetching banks')
                }), response.status_code

            banks = response.json().get('data', [])

            return jsonify({
                'code': 200,
                'status_message': 'success',
                'data': banks
            }), 200

        except Exception as e:
            return jsonify({
                'code': 500,
                'status_message': 'server error',
                'message': f'an error occurred: {str(e)}'
            }), 500

