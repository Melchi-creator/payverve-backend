"""
server.py
Application entry point
Holds all necessary configuration
"""

from flask import Flask
from flask_blueprint import Blueprint
from flask_migrate import Migrate
from flask_talisman import Talisman

import config
import routes
from models import db

server = Flask(__name__)
server.secret_key = config.secret_key
Talisman(server)

db.init_app(server)
db.app = server
migrate = Migrate(server, db)

for blueprint in vars(routes).values():
    if isinstance(blueprint, Blueprint):
        server.register_blueprint(
            blueprint, url_prefix=config.app_root)

if __name__ == '__main__':
    server.debug = config.debug if config.env == 'dev' else False
    if config.env == 'dev':
        server.run(host=config.app_host, port=config.app_port)
