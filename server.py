"""
src/server.py
This module initializes the Flask application, sets up configurations, and registers blueprints.
It also configures CORS, database migrations, and security features.
It serves as the entry point for the application, allowing it to run in development mode.
"""

from flask import Flask
from flask.blueprints import Blueprint
from flask_cors import CORS
from flask_migrate import Migrate
from flask_talisman import Talisman

import config
from src import routes
from src.models import CurrencyModel, db

import os


server = Flask(__name__)
server.secret_key = config.secret_key
Talisman(server, force_https=False)

server.config["SQLALCHEMY_DATABASE_URI"] = config.database_uri
server.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = config.database_tracker
server.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,
    "pool_recycle": 300,
    "pool_size": 5,
    "max_overflow": 2,
    "connect_args": {
        "sslmode": "require",
        "connect_timeout": 10,
    },
    "execution_options": {
        "prepared_statement_cache_size": 0
    }
}

db.init_app(server)
db.app = server
migrate = Migrate(server, db)

# with server.app_context():
#     auth.init_app(app=server, db=db)
#     from . import error_handlers

allowed_origins = [
    config.mobile_app_path
]

cors = CORS(server,
            resources={r"/payverve/*": {"origins": allowed_origins}},
            methods=["POST", "GET", "PUT", "DELETE"],
            allow_headers=["Authorization", "Content-Type"],
            supports_credentials=True,
            max_age=3600)

for blueprint in vars(routes).values():
    if isinstance(blueprint, Blueprint):
        server.register_blueprint(
            blueprint, url_prefix=config.app_root)

with server.app_context():
    check_currenies = CurrencyModel.query.all()

    if not check_currenies:
        # noinspection  PyArgumentList
        ngn_currency = CurrencyModel(
            name="Nigerian Naira",
            short_code="ngn",
            country="Nigeria",
        )
        ngn_currency.save()

        # noinspection  PyArgumentList
        usd_currency = CurrencyModel(
            name="United States Dollar",
            short_code="usd",
            country="United States",
        )
        usd_currency.save()

        # noinspection  PyArgumentList
        gbp_currency = CurrencyModel(
            name="Great Britain Pound",
            short_code="gbp",
            country="United Kingdom",
        )
        gbp_currency.save()

if __name__ == "__main__":
    server.debug = config.debug if config.env == "dev" else False
    if config.env == "dev":
        server.run(host=config.app_host, port=config.app_port)
