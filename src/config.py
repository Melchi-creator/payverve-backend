"""
config.py

All configuration required for the app to successfully run
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