"""
src/server.py
This module initializes the Flask application, sets up configurations, and registers blueprints.
It also configures CORS, database migrations, and security features.
It serves as the entry point for the application, allowing it to run in development mode.
"""

from flask import Flask
from flask.blueprints import Blueprint
import os

from src.db_defaults import DBDefaults
from src.models import CurrencyModel, db
from src import routes
import config
from sqlalchemy.pool import NullPool
from flask_talisman import Talisman
from flask_migrate import Migrate
from flask_cors import CORS


server = Flask(__name__)
server.secret_key = config.secret_key
Talisman(server, force_https=config.debug if config.env == "prod" else False)

server.config["SQLALCHEMY_DATABASE_URI"] = config.database_uri
server.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = config.database_tracker

engine_options = {
    "poolclass": NullPool,
    "connect_args": {
        "connect_timeout": 10,
    }
}

# Only require SSL for remote (production) databases
if (
    config.database_uri
    and "localhost" not in config.database_uri
    and "127.0.0.1" not in config.database_uri
):
    engine_options["connect_args"]["sslmode"] = "require"

server.config["SQLALCHEMY_ENGINE_OPTIONS"] = engine_options

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
    DBDefaults.currency_defaults()


if __name__ == "__main__":
    server.debug = config.debug if config.env == "dev" else False
    if config.env == "dev":
        server.run(host=config.app_host, port=config.app_port)
