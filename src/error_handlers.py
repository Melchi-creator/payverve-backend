from flask import current_app as app, jsonify
from sqlalchemy.exc import (DataError, DisconnectionError, IntegrityError,
                            InternalError, OperationalError, ProgrammingError,
                            SQLAlchemyError)


@app.errorhandler(400)
def bad_request_handler(e):
    status_message = e.data['status_message'] if getattr(e, 'data', None) else e.description.split(':')[0]

    return jsonify({
        'code': 400,
        'status_message': 'bad request',
        'message': status_message
    }), 400


@app.errorhandler(404)
def not_found_handler(e):
    return jsonify({
        'code': 404,
        'status_message': 'url not found'
    }), 404


@app.errorhandler(405)
def method_not_allowed_handler(e):
    return jsonify({
        'code': 405,
        'status_message': 'method not allowed for requested url'
    }), 405


@app.errorhandler(500)
def server_error_handler(e):
    return jsonify({
        'code': 500,
        'status_message': 'something went wrong!'
    }), 500


@app.errorhandler(InternalError)
def internal_error_handler(e):
    return jsonify({
        'code': 500,
        'status_message': 'internal server - internal server error',
        'message': 'could not fetch data'
    }), 500


@app.errorhandler(OperationalError)
def operational_error_handler(e):
    return jsonify({
        'code': 500,
        'status_message': 'database error - operation error',
        'message': 'could not fetch data'
    }), 500


@app.errorhandler(SQLAlchemyError)
def SQLAlchemy_error_handler(e):
    return jsonify({
        'code': 500,
        'status_message': 'database error - sqlalchemy error',
        'message': 'could not fetch data'
    }), 500


@app.errorhandler(DisconnectionError)
def disconnection_error_handler(e):
    return jsonify({
        'code': 500,
        'status_message': 'database error - disconnection error',
        'message': 'could not fetch data'
    }), 500


@app.errorhandler(ProgrammingError)
def programming_error_handler(e):
    return jsonify({
        'code': 500,
        'status_message': 'database error - programming error',
        'message': 'could not fetch table'
    }), 500


@app.errorhandler(IntegrityError)
def intergrity_error_handler(e):
    return jsonify({
        'code': 409,
        'status_message': 'conflict - integrity error',
        'message': 'account already has an account'
    }), 409


@app.errorhandler(DataError)
def data_error_handler(e):
    return jsonify({
        'code': 400,
        'status_message': 'bad request - data error',
        'message': 'ensure input data are correct'
    }), 400
