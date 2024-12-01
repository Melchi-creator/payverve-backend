"""authentication_authorisation.py

Keyword arguments:
argument -- description
Return: return_description
"""

from flask.json import jsonify
from flask_restful import Resource
from flask_restful.reqparse import Argument
from sqlalchemy.exc import DataError, \
    DisconnectionError, \
    IntegrityError, \
    InternalError, \
    OperationalError, \
    ProgrammingError, SQLAlchemyError

from ..models import AdminModel
from ..utilities import parse_params


class AuthResource(Resource):
    """ The class defines the auth resources  """

    # Admin

    @staticmethod
    @parse_params(
        Argument("email_address", location="json",
                 help="The email address of the business"),
        Argument("mobile_number", location="json",
                 help="The mobile number of the business"),
        Argument("password", location="json", required=True,
                 help="The password of the business"),
    )
    def admin_login(email_address, mobile_number, password):
        """ this function defines the admin auth """

        try:
            user_email_address = AdminModel.query.filter_by(email_address=email_address).first()
            user_mobile_number = AdminModel.query.filter_by(mobile_number=mobile_number).first()

            user_account = None

            if not email_address and not mobile_number:
                return jsonify({
                    "code": 409,
                    "error_message": "Bad Request",
                    "message": "Check your request email_address or mobile_number key is missing."  # noqa
                }), 409

            if email_address and user_email_address:
                user_account = user_email_address

            if email_address and not user_account:
                return jsonify({
                    "code": 404,
                    "error_message": "Not Found",
                    "message": f"The account you are trying to access with {email_address} was not found."  # noqa
                }), 404

            if mobile_number and user_mobile_number:
                user_account = user_mobile_number

            if mobile_number and not user_account:
                return jsonify({
                    "code": 404,
                    "error_message": "Not Found",
                    "message": f"The account you are trying to access with {mobile_number} was not found."  # noqa
                }), 404

            user_password = user_account.check_password(password)

            if not user_password:
                return jsonify({
                    "message": "Incorrect Password",
                }), 401

            if user_account.email_verified is False:
                return jsonify({
                    "message": "Your Account with us is not Verified",
                }), 401

            # datetime_used = RemoteDateTime.remote_datetime()
            #
            # auth_unique_id = secrets.token_urlsafe(8)
            # # start - access token creation
            # auth_token = user_account.encode_token(
            #     str(user_account.id), user_account.first_name,
            #     user_account.last_name, auth_unique_id)
            #
            # expires = (datetime_used + timedelta(
            #     seconds=int(config.token_expiration))
            # ).strftime("%d-%m-%Y, %I:%M %p")
            # # end - access token creation
            #
            # auth_unique_id = secrets.token_urlsafe(16)
            # # start - refresh token creation
            # auth_refresh_token = user_account.encode_refresh_token(
            #     str(user_account.id), user_account.first_name,
            #     user_account.last_name, auth_unique_id)
            #
            # expires_refresh = (datetime_used + timedelta(
            #     seconds=int(config.refresh_token_expiration))
            # ).strftime("%d-%m-%Y, %I:%M %p")
            # # end - refresh token creation

            if user_account:
                if user_password:
                    return jsonify({
                        "code": 200,
                        'status': 'success',
                        'message': f'Successfully logged in as {account}.',  # noqa
                        # 'auth_token': auth_token,
                        # 'token_expires_by': expires,
                        # 'refresh_token': auth_refresh_token,
                        # 'refresh_token_expires_by': expires_refresh,
                        # 'token_id': token_validtion.id,
                        'user': {
                            'id': user_account.id,
                            'first_name': user_account.first_name,
                            'last_name': user_account.last_name,
                            'phone_number': user_account.mobile_number,
                            'email_address': user_account.email_address,
                            'created_at': user_account.created_at,
                            'updated_at': user_account.updated_at
                        }
                    }), 200

        except IntegrityError:
            return jsonify({
                'code': 409,
                'code_status': 'conflict - integrity error',
                'data': 'account already has an account'
            }), 409

        except DataError:
            return jsonify({
                'code': 400,
                'code_status': 'bad request - data error',
                'data': 'ensure input data are correct'
            }), 400

        except InternalError:
            return jsonify({
                'code': 500,
                'code_status': 'internal server - internal server error',
                'data': 'could not fetch data'
            }), 500

        except (OperationalError, DisconnectionError, SQLAlchemyError):
            return jsonify({
                'code': 500,
                'code_status': 'database error - operation, sqlalchemy and disconnection error',
                'data': 'could not fetch data'
            }), 500

        except ProgrammingError:
            return jsonify({
                'code': 500,
                'code_status': 'database error - programming error',
                'data': 'could not fetch table'
            }), 500

    # Customer

    # @staticmethod
    # @parse_params(
    #     Argument("email_address", location="json",
    #              help="The email address of the customer."),
    #     Argument("mobile_number", location="json",
    #              help="The mobile number of the customer."),
    #     Argument("password", location="json", required=True,
    #              help="The password of the customer."),
    # )
    # def customer_login(email_address, mobile_number, password):
    #     """ """
    #
    #     try:
    #
    #         customer_email = CustomerModel.query.filter_by(
    #             email_address=email_address).first()
    #
    #         customer_mobile = CustomerModel.query.filter_by(
    #             mobile_number=mobile_number).first()
    #
    #         if email_address and not customer_email:
    #             return jsonify({
    #                 "message": "Email Not Found",
    #             }), 404
    #
    #         if mobile_number and not customer_mobile:
    #             return jsonify({
    #                 "message": "Mobile Number Not Found",
    #             }), 404
    #
    #         if mobile_number and customer_mobile:
    #             customer_email = customer_mobile
    #
    #         if not email_address and not mobile_number:
    #             return jsonify({
    #                 "message": "Email or Mobile Number is missing",
    #             }), 404
    #
    #         customer_password = customer_email.check_password(password)
    #
    #         token_check = TokenValidationModel.query.filter_by(user_id=customer_email.id).first()  # noqa
    #
    #         if token_check and token_check.active is True:
    #             token_check.active = False
    #             token_check.blacklist_access_token = True
    #             token_check.blacklist_refresh_token = True
    #             token_check.save()
    #
    #         if not customer_password:
    #             return jsonify({
    #                 "message": "Incorrect Password",
    #             }), 403
    #
    #         if customer_email.email_verified is False:
    #             return jsonify({
    #                 "message": "Your Account with us is not Verified",
    #             }), 401
    #
    #         auth_unique_id = secrets.token_urlsafe(16)
    #
    #         datetime_used = RemoteDateTime.remote_datetime()
    #
    #         # start - access token creation
    #         auth_token = customer_email.encode_token(
    #             str(customer_email.id), customer_email.first_name,
    #             customer_email.last_name, auth_unique_id)
    #
    #         expires = (datetime_used + timedelta(
    #             seconds=int(config.token_expiration))
    #                    ).strftime("%d-%m-%Y, %I:%M %p")
    #         # end - access token creation
    #
    #         refresh_unique_id = secrets.token_urlsafe(8)
    #
    #         # start - refresh token creation
    #         auth_refresh_token = customer_email.encode_refresh_token(
    #             str(customer_email.id), customer_email.first_name,
    #             customer_email.last_name, refresh_unique_id)
    #
    #         expires_refresh = (datetime_used + timedelta(
    #             seconds=int(config.refresh_token_expiration))
    #                            ).strftime("%d-%m-%Y, %I:%M %p")
    #         # end - refresh token creation
    #
    #         if customer_email:
    #             if customer_password:
    #                 user_role = RoleModel.query.filter_by(
    #                     id=customer_email.role_id).first()
    #
    #                 token_validtion = TokenValidationModel(
    #                     access_token=auth_token,
    #                     refresh_token=auth_refresh_token,
    #                     user_id=customer_email.id,
    #                     active=True
    #                 )
    #                 token_validtion.save()
    #
    #                 return jsonify({
    #                     "code": 200,
    #                     'status': 'success',
    #                     'message': 'Successfully logged in as customer.',
    #                     'auth_token': auth_token,
    #                     'token_expires_by': expires,
    #                     'refresh_token': auth_refresh_token,
    #                     'refresh_token_expires_by': expires_refresh,
    #                     'token_id': token_validtion.id,
    #                     'user': {
    #                         'id': customer_email.id,
    #                         'first_name': customer_email.first_name,
    #                         'last_name': customer_email.last_name,
    #                         'photo': customer_email.photo,
    #                         'phone_number': customer_email.mobile_number,
    #                         'email_address': customer_email.email_address,
    #                         'role': user_role.role,
    #                         'created_at': customer_email.created_at,
    #                         'updated_at': customer_email.updated_at
    #                     }
    #                 }), 200
    #
    #     except Forbidden as e:
    #         return {
    #             'Code': e.code,
    #             'Type': e.type,
    #             'Error_Message': e.message
    #         }
    #
    #     except DataNotFound as e:
    #         return {
    #             'Code': e.code,
    #             'Type': e.type,
    #             'Error_Message': e.message,
    #             'Message': "No customer data was found in the database."
    #         }
    #
    #     except InternalServerError as e:
    #         return {
    #             'Code': e.code,
    #             'Type': e.type,
    #             'Error_Message': e.message
    #         }
    #
    # # google auth
    #
    # @staticmethod
    # def customer_google_auth():
    #     auth_url, state = flow.authorization_url()
    #     role = request.args.get('role')
    #
    #     session["state"] = state
    #     session["role"] = role
    #     return redirect(auth_url)
    #
    # @staticmethod
    # def customer_google_callback():
    #     flow.fetch_token(authorization_response=request.url)
    #
    #     if not session["state"] == request.args["state"]:
    #         return jsonify({
    #             "code": 400,
    #             "status": "Bad Request",
    #             "message": "Invalid state parameter."
    #         })
    #
    #     credentials = flow.credentials
    #     request_session = requests.session()
    #     cached_session = cachecontrol.CacheControl(request_session)
    #     token_request = google.auth.transport.requests.Request(
    #         session=cached_session)
    #
    #     time.sleep(2)
    #
    #     try:
    #         id_info = id_token.verify_oauth2_token(
    #             id_token=credentials._id_token,
    #             request=token_request,
    #             audience=google_client_id
    #         )
    #     except google.auth.exceptions.InvalidValue:
    #         return jsonify({
    #             "code": 400,
    #             "status": "Bad Request",
    #             "message": "Token validation error. Please ensure your system clock is correct."  # noqa
    #         }), 400
    #
    #     check_user_email = None
    #
    #     role = session.get("role")
    #
    #     # login setup
    #
    #     if role is not None and role == config.two:
    #         check_user_email = CustomerModel.query.filter_by(
    #             email_address=id_info.get("email")).first()
    #
    #     if role is not None and role == config.four:
    #         check_user_email = BusinessModel.query.filter_by(
    #             email_address=id_info.get("email")).first()
    #
    #     if role is None:
    #         check_employee = EmployeeModel.query.filter_by(
    #             email_address=id_info.get("email")).first()
    #
    #         check_admin = AdminModel.query.filter_by(
    #             email_address=id_info.get("email")).first()
    #
    #         if check_employee:
    #             check_user_email = check_employee
    #
    #         if check_admin:
    #             check_user_email = check_admin
    #
    #     if check_user_email and check_user_email.google_id is None:
    #         check_user_email.google_id = id_info.get("sub")
    #         check_user_email.save()
    #
    #     # registration setup
    #
    #     if not check_user_email and not role:
    #         return jsonify({
    #             "code": 404,
    #             "status": "Not Found",
    #             "message": "No employee or admin data was found",
    #         })
    #
    #     if not check_user_email and role == config.two:
    #         new_customer = CustomerModel(
    #             first_name=id_info.get("given_name"),
    #             last_name=id_info.get("family_name"),
    #             email_address=id_info.get("email"),
    #             mobile_number=id_info.get("phone_number"),
    #             google_id=id_info.get("sub")
    #         )
    #         new_customer.set_password(secrets.token_urlsafe(16))
    #         new_customer.save()
    #
    #         check_user_email = CustomerModel.query.filter_by(
    #             email_address=new_customer.email_address).first()
    #
    #     if not check_user_email and role == config.four:
    #         new_business = BusinessModel(
    #             first_name=id_info.get("given_name"),
    #             last_name=id_info.get("family_name"),
    #             email_address=id_info.get("email"),
    #             mobile_number=id_info.get("phone_number"),
    #             google_id=id_info.get("sub")
    #         )
    #         new_business.set_password(secrets.token_urlsafe(16))
    #         new_business.save()
    #
    #         check_user_email = BusinessModel.query.filter_by(
    #             email_address=new_business.email_address).first()
    #
    #     session["google_id"] = id_info.get("sub")
    #     session["first_name"] = id_info.get("given_name")
    #     session["last_name"] = id_info.get("family_name")
    #     session["role"] = role
    #     session.modified = True
    #
    #     datetime_used = RemoteDateTime.remote_datetime()
    #
    #     expires = (datetime_used + timedelta(
    #         seconds=int(config.token_expiration))
    #                ).strftime("%H:%M")
    #
    #     return jsonify({
    #         "code": 200,
    #         'status': 'success',
    #         'message': 'Request was Successful.',
    #         'auth_token': credentials._id_token,
    #         'token_expires_by': expires,
    #         'user': {
    #             'id': check_user_email.id,
    #             'first_name': id_info.get("given_name"),
    #             'last_name': id_info.get("family_name"),
    #             'photo': check_user_email.photo,
    #             'phone_number': check_user_email.mobile_number,
    #             'email_address': id_info.get("email")
    #         }
    #     })
    #
    # @staticmethod
    # @parse_params(
    #     Argument("user_id", location="json", required=True,
    #              help="The current password of the user"),
    # )
    # def customer_google_logout(user_id):
    #     access_tokens = TokenValidationModel.query.filter_by(user_id=user_id, active=True).first()  # noqa
    #
    #     if not access_tokens:
    #         return jsonify({
    #             "code": 404,
    #             "status": "Not Found",
    #             "message": "No user data was found",
    #         })
    #
    #     if access_tokens:
    #         access_tokens.active = False
    #         access_tokens.blacklist_access_token = True
    #         access_tokens.blacklist_refresh_token = True
    #         access_tokens.save()
    #
    #     session.clear()
    #     session.modified = True
    #     return jsonify({
    #         "code": 200,
    #         'status': 'success',
    #         'message': 'Successfully logged out.'
    #     })
