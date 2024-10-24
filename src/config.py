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

exchange_rate_api_key = os.getenv('EXCHANGERATE_API_KEY')
exchange_rate_api_url = os.getenv('EXCHANGERATE_API_URL')
exchange_rate_markup = os.getenv('EXCHANGERATE_MARKUP')
