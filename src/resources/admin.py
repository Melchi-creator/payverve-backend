"""
AdminResource
admin.py

Defines all functions for admin admins especially CRUD
"""
from flask import jsonify
from flask_restful import Resource
from flask_restful.reqparse import Argument

from ..models import AdminModel
from ..utilities import parse_params


class AdminResource(Resource):
    """ This class is concern with admin Resources """

    @staticmethod
    @parse_params(
        Argument("first_name", location="json", required=True),
        Argument("last_name", location="json", required=True),
        Argument("email_address", location="json", required=True),
        Argument("mobile_number", location="json", required=True),
        Argument("password", location="json", required=True),
        Argument("gender", location="json", required=True),
        Argument("date_of_birth", location="json", required=True),
        Argument("admin_role", location="json", required=True),
    )
    def create(first_name, last_name, email_address, mobile_number, password, gender, date_of_birth, admin_role):
        """ Creates admins account """

        admin_model = AdminModel.query
        admin_email = admin_model.filter_by(email_address=email_address).first()
        admin_number = admin_model.filter_by(mobile_number=mobile_number).first()

        if admin_email:
            return jsonify({
                'code': 409,
                'code_status': 'conflict',
                'data': 'email address already has an account'
            }), 409

        if admin_number:
            return jsonify({
                'code': 409,
                'code_status': 'conflict',
                'data': 'mobile number already has an account'
            }), 409

        # noinspection PyArgumentList
        new_admin = AdminModel(
            first_name=first_name,
            last_name=last_name,
            email_address=email_address,
            mobile_number=mobile_number,
            gender=gender,
            date_of_birth=date_of_birth,
            admin_role=admin_role
        )
        new_admin.set_password(password)
        new_admin.save()

        # # function to generate account validation token
        # token = validation.generate_token(new_admin.get_id())
        # verification_url = config.base_url + url_for('admin.verify_email', token=token)
        # template = render_template('welcome.html', first_name=new_admin.first_name, token=verification_url)
        # data = {
        #     'recipient': new_admin.email_address,
        #     'subject': 'Welcome to PayVerve',
        #     'template': template
        # }
        #
        # # Mail sending should be handled as background task
        # # TODO: Integrete with Celery/Redis for task scheduling
        # emailHandler.sendMail(**data)

        return jsonify({
            'code': 201,
            'code_status': 'created',
            'data': 'admin account was successfully created',
            # 'token': token
        }), 201

    @staticmethod
    def read_all():
        """ Retrieve all admins account """

        admins = AdminModel.query.all()

        if not admins:
            return jsonify({
                'code': 404,
                'code_status': 'data not found',
                'data': 'no admin account was found'
            }), 404

        data = []

        for admin in admins:
            data.append({
                'id': admin.id,
                'first_name': admin.first_name,
                'last_name': admin.last_name,
                'middle_name': admin.middle_name,
                'email_address': admin.email_address,
                'mobile_number': admin.mobile_number,
                'password': admin.password,
                'gender': admin.gender,
                'date_of_birth': admin.date_of_birth,
                'house_number': admin.house_number,
                'street_name': admin.street_name,
                'city': admin.city,
                'state': admin.state,
                'zipcode': admin.zipcode,
                'country': admin.country,
                'photo': admin.photo,
                'admin_role': admin.admin_role
            })

        return jsonify({
            'code': 200,
            'code_status': 'success',
            'data': data
        }), 200

    @staticmethod
    # @auth.login_required
    def read_one(id=None):
        """ Retrieve a admin account by id """

        admin = AdminModel.query.filter_by(id=id).first()

        if not admin:
            return jsonify({
                'code': 404,
                'code_status': 'data not found',
                'data': 'no admin account was found'
            }), 404

        data = {
            'id': admin.id,
            'first_name': admin.first_name,
            'last_name': admin.last_name,
            'middle_name': admin.middle_name,
            'email_address': admin.email_address,
            'mobile_number': admin.mobile_number,
            'password': admin.password,
            'gender': admin.gender,
            'date_of_birth': admin.date_of_birth,
            'house_number': admin.house_number,
            'street_name': admin.street_name,
            'city': admin.city,
            'state': admin.state,
            'zipcode': admin.zipcode,
            'country': admin.country,
            'photo': admin.photo,
            'admin_role': admin.admin_role,
            'verified': admin.email_verified
        }

        return jsonify({
            'code': 200,
            'code_status': 'success',
            'data': data
        }), 200

    @staticmethod
    @parse_params(
        Argument("first_name", location="json"),
        Argument("last_name", location="json"),
        Argument("middle_name", location="json"),
        Argument("email_address", location="json"),
        Argument("mobile_number", location="json"),
        Argument("password", location="json"),
        Argument("gender", location="json"),
        Argument("date_of_birth", location="json"),
        Argument("house_number", location="json"),
        Argument("street_name", location="json"),
        Argument("city", location="json"),
        Argument("state", location="json"),
        Argument("zipcode", location="json"),
        Argument("country", location="json"),
        Argument("photo", location="json"),
        Argument("admin_role", location="json"),
    )
    def update(id=None, **fields):
        """ Updates a admin account by id """

        admin = AdminModel.query.filter_by(id=id).first()

        if not admin:
            return jsonify({
                'code': 404,
                'code_status': 'data not found',
                'data': 'no admin account was found'
            }), 404

        for (key, value) in fields.items():
            if value is not None:
                setattr(admin, key, value)

        admin.save()

        data = {
            'id': admin.id,
            'first_name': admin.first_name,
            'last_name': admin.last_name,
            'middle_name': admin.middle_name,
            'email_address': admin.email_address,
            'mobile_number': admin.mobile_number,
            'password': admin.password,
            'gender': admin.gender,
            'date_of_birth': admin.date_of_birth,
            'house_number': admin.house_number,
            'street_name': admin.street_name,
            'city': admin.city,
            'state': admin.state,
            'zipcode': admin.zipcode,
            'country': admin.country,
            'photo': admin.photo,
            'admin_role': admin.admin_role,
        }

        return jsonify({
            'code': 200,
            'code_status': 'success',
            'data': data
        }), 200

    @staticmethod
    # @auth.login_required
    def delete(id=None, **kwargs):
        """ Retrieve and delete a admin account by id """

        admin = AdminModel.query.filter_by(id=id).first()

        if not admin:
            return jsonify({
                'code': 404,
                'code_status': 'data not found',
                'data': 'no admin account was found'
            }), 404

        admin.delete()

        return jsonify({
            'code': 200,
            'code_status': 'success',
            'data': 'admin ccount has been deleted'
        }), 200

    # @staticmethod
    # @parse_params(
    #     Argument("email_address", location="json", required=True),
    #     Argument("password", location="json", required=True),
    # )
    # def login(email_address, password):
    #     """ Retrieve a admin account by id """
    #
    #     admin: AdminModel = AdminModel.query.filter_by(email_address=email_address).first()
    #
    #     if not admin:
    #         return jsonify({
    #             'code': 404,
    #             'code_status': 'data not found',
    #             'data': 'no admin account was found'
    #         }), 404
    #
    #     if admin and admin.check_password(password=password):
    #         return auth.login(user=admin)
    #
    #     return jsonify({
    #         'code': 401,
    #         'code_status': 'Invalid credentials',
    #     }), 401
    #
    # @staticmethod
    # @auth.login_required
    # def logout(**kwargs):
    #     """ Logs out the current admin account"""
    #     return auth.logout()
    #
    # @staticmethod
    # def verify_email(token=None):
    #     user_id = validation.verify_token(token)
    #     admin_user = AdminModel.query.filter_by(id=user_id).first()
    #     if admin_user:
    #         admin_user.email_verified = True
    #         admin_user.save()
    #         return jsonify({
    #             "code": 200,
    #             "status": "Account verified"
    #         }), 200
    #
    #     return ({
    #         "code": 400,
    #         "status": "Invalid Token!"
    #     }), 400
    #
    # @staticmethod
    # @parse_params(
    #     Argument("email_address", location="json", required=True),
    # )
    # def request_password_reset(email_address):
    #     admin = AdminModel.query.filter_by(email_address=email_address).first()
    #
    #     if not admin:
    #         return jsonify({
    #             'code': 404,
    #             'code_status': 'data not found',
    #             'data': 'no account with that email'
    #         }), 404
    #
    #     token = validation.generate_token(admin.get_id(), context='reset-password')
    #     # request url should be deeplink to app
    #     reset_url = config.mobile_app_path + url_for('admin.verify_reset_token', token=token)
    #     date_time = datetime.now().strftime('%a %d %b %Y, %I:%M%p')
    #     date, time = date_time.split(', ')
    #
    #     context = {
    #         'first_name': admin.first_name,
    #         'reset_link': reset_url,
    #         'date': date,
    #         'time': time
    #     }
    #     print(context)
    #
    #     reset_template = render_template('resetpassword.html', **context)
    #     reset_data = {
    #         'recipient': admin.email_address,
    #         'subject': 'Account Login',
    #         'template': reset_template
    #     }
    #
    #     # Mail sending should be handled as background task
    #     # TODO: Integrete with Celery/Redis for task scheduling
    #     emailHandler.sendMail(**reset_data)
    #
    #     return jsonify({
    #         'code': 200,
    #         'code_status': 'email sent',
    #         'data': 'reset link sent to registered email',
    #         'url': reset_url
    #     }), 200
    #
    # @staticmethod
    # def verify_reset_token():
    #     token = request.args.get('token')
    #     admin_id = validation.verify_token(token=token, context='reset-password')
    #     admin = AdminModel.query.filter_by(id=admin_id).first()
    #
    #     if not admin:
    #         return jsonify({
    #             'code': 401,
    #             'data': "Token is invalid or expired!"
    #         }), 401
    #
    #     return jsonify({
    #         'code': 202,
    #         'data': 'Token is valid',
    #     }), 202
    #
    # @staticmethod
    # @parse_params(
    #     Argument("new_password", location="json", required=True),
    #     Argument("token", location="json", required=True),
    # )
    # def reset_password(new_password=None, token=None):
    #     token = token if request.method == 'POST' else request.args.get('token')
    #     admin_id = validation.verify_token(token=token, context='reset-password')
    #     admin = AdminModel.query.filter_by(id=admin_id).first()
    #
    #     if not admin:
    #         return jsonify({
    #             'code': 401,
    #             'data': "Token is invalid or expired!"
    #         }), 401
    #
    #     admin.set_password(password=new_password)
    #     admin.save()
    #
    #     return jsonify({
    #         'code': 200,
    #         'data': 'password reset successful',
    #     }), 200
