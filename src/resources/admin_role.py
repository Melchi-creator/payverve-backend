"""
admin_roles.py

Defines all functions for admin roles, especially CRUD
"""

from flask import jsonify
from flask_restful import Resource
from flask_restful.reqparse import Argument
from sqlalchemy.exc import (DataError, DisconnectionError, IntegrityError,
                            InternalError, OperationalError, ProgrammingError,
                            SQLAlchemyError)

from ..models import AdminRoleModel
from ..utilities import parse_params


class AdminRoleResource(Resource):
    """ This class defines resource methods for admin roles. """

    @staticmethod
    @parse_params(
        Argument('role', location='json', required=True)
    )
    def create(role):
        """ Creates a new admin role """

        try:
            _role = AdminRoleModel.query.filter_by(role=role).first()

            if _role:
                return jsonify({
                    'code': 409,
                    'status_message': 'conflict',
                    'message': 'this admin role already exists'
                }), 409

            # noinspection PyArgumentList
            new_role = AdminRoleModel(
                role=role
            )
            new_role.save()

            return jsonify({
                'code': 201,
                'status_message': 'created',
                'message': 'admin role was successfully added'
            }), 201

        except IntegrityError:
            return jsonify({
                'code': 409,
                'status_message': 'conflict - integrity error',
                'message': 'this admin role already exists'
            }), 409

        except DataError:
            return jsonify({
                'code': 400,
                'status_message': 'bad request - data error',
                'message': 'ensure input data are correct'
            }), 400

        except InternalError:
            return jsonify({
                'code': 500,
                'status_message': 'internal server - internal server error',
                'message': 'could not fetch data'
            }), 500

        except (OperationalError, DisconnectionError, SQLAlchemyError):
            return jsonify({
                'code': 500,
                'status_message': 'database error - operation, sqlalchemy and disconnection error',
                'message': 'could not fetch data'
            }), 500

        except ProgrammingError:
            return jsonify({
                'code': 500,
                'status_message': 'database error - programming error',
                'message': 'could not fetch table'
            }), 500

    @staticmethod
    def read_all():
        """ Retrieves all admin roles """

        try:
            roles = AdminRoleModel.query.all()

            if not roles:
                return jsonify({
                    'code': 404,
                    'status_message': 'data not found',
                    'message': 'no admin role was found'
                }), 404

            data = [{'id': role.id, 'role': role.role} for role in roles]

            return jsonify({
                'code': 200,
                'status_message': 'success',
                'data': data
            }), 200

        except InternalError:
            return jsonify({
                'code': 500,
                'status_message': 'internal server - internal server error',
                'message': 'could not fetch data'
            }), 500

        except (OperationalError, DisconnectionError):
            return jsonify({
                'code': 500,
                'status_message': 'database error - operation and disconnection error',
                'message': 'could not fetch data'
            }), 500

        except ProgrammingError:
            return jsonify({
                'code': 500,
                'status_message': 'database error - programming error',
                'message': 'could not fetch table'
            }), 500

    @staticmethod
    def read_one(id=None):
        """ Retrieves an admin role by id """

        try:
            role = AdminRoleModel.query.filter_by(id=id).first()

            if not role:
                return jsonify({
                    'code': 404,
                    'status_message': 'data not found',
                    'message': 'no role with this id was found'
                }), 404

            data = {
                'id': role.id,
                'role': role.role
            }

            return jsonify({
                'code': 200,
                'status_message': 'success',
                'data': data
            }), 200

        except InternalError:
            return jsonify({
                'code': 500,
                'status_message': 'internal server - internal server error',
                'message': 'could not fetch data'
            }), 500

        except (OperationalError, DisconnectionError):
            return jsonify({
                'code': 500,
                'status_message': 'database error - operation and disconnection error',
                'message': 'could not fetch data'
            }), 500

        except ProgrammingError:
            return jsonify({
                'code': 500,
                'status_message': 'database error - programming error',
                'message': 'could not fetch table'
            }), 500

    @staticmethod
    @parse_params(
        Argument('role', location='json', required=True)
    )
    def update(id=None, **fields):
        """ Update a role by id """

        try:
            role = AdminRoleModel.query.filter_by(id=id).first()

            if not role:
                return jsonify({
                    'code': 404,
                    'status_message': 'data not found',
                    'message': 'no role with this id was found'
                }), 404

            role.role = fields['role']
            role.save()

            data = {
                'id': role.id,
                'role': role.role
            }

            return jsonify({
                'code': 200,
                'status_message': 'success',
                'data': data
            }), 200

        except InternalError:
            return jsonify({
                'code': 500,
                'status_message': 'internal server - internal server error',
                'message': 'could not fetch data'
            }), 500

        except (OperationalError, DisconnectionError):
            return jsonify({
                'code': 500,
                'status_message': 'database error - operation and disconnection error',
                'message': 'could not fetch data'
            }), 500

        except ProgrammingError:
            return jsonify({
                'code': 500,
                'status_message': 'database error - programming error',
                'message': 'could not fetch table'
            }), 500

    @staticmethod
    def delete(id=None):
        """ Retrieve and delete an admin role by id """

        try:
            role = AdminRoleModel.query.filter_by(id=id).first()

            if not role:
                return jsonify({
                    'code': 404,
                    'status_message': 'data not found',
                    'message': 'no role with this id was found'
                }), 404

            role.delete()

            return jsonify({
                'code': 200,
                'status_message': 'success',
                'message': 'admin role was deleted successfully'
            }), 200

        except InternalError:
            return jsonify({
                'code': 500,
                'status_message': 'internal server - internal server error',
                'message': 'could not fetch data'
            }), 500

        except (OperationalError, DisconnectionError):
            return jsonify({
                'code': 500,
                'status_message': 'database error - operation and disconnection error',
                'message': 'could not fetch data'
            }), 500

        except ProgrammingError:
            return jsonify({
                'code': 500,
                'status_message': 'database error - programming error',
                'message': 'could not fetch table'
            }), 500
