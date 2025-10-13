from flask import current_app as app, jsonify
from sqlalchemy.exc import (DataError, DisconnectionError, IntegrityError,
                            InternalError, OperationalError, ProgrammingError,
                            SQLAlchemyError)


@app.errorhandler(400)
def bad_request_handler(e):
    message = e.data['message'] if getattr(e, 'data', None) else e.description.split(':')[0]

    return jsonify({
        'code': 400,
        'message': 'bad request',
        'details': message
    }), 400


@app.errorhandler(404)
def not_found_handler(e):
    return jsonify({
        'code': 404,
        'message': 'url not found'
    }), 404


@app.errorhandler(405)
def method_not_allowed_handler(e):
    return jsonify({
        'code': 405,
        'message': 'method not allowed for requested url'
    }), 405


@app.errorhandler(500)
def server_error_handler(e):
    return jsonify({
        'code': 500,
        'message': 'something went wrong!'
    }), 500


@app.errorhandler(InternalError)
def internal_error_handler(e):
    return jsonify({
        'code': 500,
        'code_status': 'internal server - internal server error',
        'message': 'could not fetch data'
    }), 500


@app.errorhandler(OperationalError)
def operational_error_handler(e):
    return jsonify({
        'code': 500,
        'code_status': 'database error - operation error',
        'message': 'could not fetch data'
    }), 500


@app.errorhandler(SQLAlchemyError)
def SQLAlchemy_error_handler(e):
    return jsonify({
        'code': 500,
        'code_status': 'database error - sqlalchemy error',
        'message': 'could not fetch data'
    }), 500


@app.errorhandler(DisconnectionError)
def disconnection_error_handler(e):
    return jsonify({
        'code': 500,
        'code_status': 'database error - disconnection error',
        'message': 'could not fetch data'
    }), 500


@app.errorhandler(ProgrammingError)
def programming_error_handler(e):
    return jsonify({
        'code': 500,
        'code_status': 'database error - programming error',
        'message': 'could not fetch table'
    }), 500


@app.errorhandler(IntegrityError)
def intergrity_error_handler(e):
    return jsonify({
        'code': 409,
        'code_status': 'conflict - integrity error',
        'message': 'account already has an account'
    }), 409


@app.errorhandler(DataError)
def data_error_handler(e):
    return jsonify({
        'code': 400,
        'code_status': 'bad request - data error',
        'message': 'ensure input data are correct'
    }), 400
