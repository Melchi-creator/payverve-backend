"""
config.py

Holds all variables configuration required for the app to successfully run
Fetch all variables from .env
"""

import os

from dotenv import load_dotenv

load_dotenv()

env = os.getenv('ENV')
secret_key = os.getenv('SECRET_KEY')
debug = os.getenv('DEBUG')

app_host = os.getenv('APP_HOST')
app_port = os.getenv('APP_PORT')
app_root = os.getenv('APP_ROOT')

database_username = os.getenv('DB_USERNAME')
database_paswword = os.getenv('DB_PASSWORD')
database_host = os.getenv('DB_HOST')
database_port = os.getenv('DB_PORT')
database_name = os.getenv('DB_NAME')

database_uri = f"postgresql://{database_username}:{database_paswword}@{database_host}:{database_port}/{database_name}"
database_tracker = False

mobile_app_path = os.getenv('MOBILE_APP_PATH')

mail_api_key = os.getenv('MAIL_API_KEY')
mail_default_sender = os.getenv('MAIL_DEFAULT_SENDER')

mj_apikey_public = os.getenv('MJ_APIKEY_PUBLIC')
mj_apikey_private = os.getenv('MJ_APIKEY_PRIVATE')