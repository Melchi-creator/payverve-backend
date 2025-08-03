"""
server.py

Application Entry Point During Development
Hold all connections and configurations
"""

from flask import Flask
from flask.blueprints import Blueprint
from flask_cors import CORS
from flask_migrate import Migrate
from flask_talisman import Talisman

from src import routes
import config
# from .middlewares.auth import auth
from src.models import db

server = Flask(__name__)
server.secret_key = config.secret_key
Talisman(server)

server.config["SQLALCHEMY_DATABASE_URI"] = config.database_uri
server.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = config.database_tracker

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

if __name__ == "__main__":
    server.debug = config.debug if config.env == "dev" else False
    if config.env == "dev":
        server.run(host=config.app_host, port=config.app_port)
