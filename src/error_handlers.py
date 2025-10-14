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
        'data': message
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
        'message': 'internal server - internal server error',
        'data': 'could not fetch data'
    }), 500


@app.errorhandler(OperationalError)
def operational_error_handler(e):
    return jsonify({
        'code': 500,
        'message': 'database error - operation error',
        'data': 'could not fetch data'
    }), 500


@app.errorhandler(SQLAlchemyError)
def SQLAlchemy_error_handler(e):
    return jsonify({
        'code': 500,
        'message': 'database error - sqlalchemy error',
        'data': 'could not fetch data'
    }), 500


@app.errorhandler(DisconnectionError)
def disconnection_error_handler(e):
    return jsonify({
        'code': 500,
        'message': 'database error - disconnection error',
        'data': 'could not fetch data'
    }), 500


@app.errorhandler(ProgrammingError)
def programming_error_handler(e):
    return jsonify({
        'code': 500,
        'message': 'database error - programming error',
        'data': 'could not fetch table'
    }), 500


@app.errorhandler(IntegrityError)
def intergrity_error_handler(e):
    return jsonify({
        'code': 409,
        'message': 'conflict - integrity error',
        'data': 'account already has an account'
    }), 409


@app.errorhandler(DataError)
def data_error_handler(e):
    return jsonify({
        'code': 400,
        'message': 'bad request - data error',
        'data': 'ensure input data are correct'
    }), 400
