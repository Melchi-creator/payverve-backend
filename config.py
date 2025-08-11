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
app_path = os.getenv('APP_PATH')

database_username = os.getenv('DB_USERNAME')
database_paswword = os.getenv('DB_PASSWORD')
database_host = os.getenv('DB_HOST')
database_port = os.getenv('DB_PORT')
database_name = os.getenv('DB_NAME')

database_uri = f"postgresql://{database_username}:{database_paswword}@{database_host}:{database_port}/{database_name}"
database_tracker = False

mobile_app_path = os.getenv('MOBILE_APP_PATH')

exchange_rate_api_url = os.getenv('EXCHANGERATE_API_URL')
exchange_rate_api_key = os.getenv('EXCHANGERATE_API_KEY')

mailtrap_base_url = os.getenv('MAILTRAP_BASE_URL')
mailtrap_api_key = os.getenv('MAILTRAP_API_KEY')
mailtrap_payverve_helpdesk_name = os.getenv('MAILTRAP_PAYVERVE_HELPDESK_NAME')
mailtrap_payverve_helpdesk_email = os.getenv('MAILTRAP_PAYVERVE_HELPDESK_EMAIL')
mailtrap_payverve_eva_name = os.getenv('MAILTRAP_PAYVERVE_EVA_NAME')
mailtrap_payverve_eva_email = os.getenv('MAILTRAP_PAYVERVE_EVA_EMAIL')
mailtrap_payverve_security_name = os.getenv('MAILTRAP_PAYVERVE_SECURITY_NAME')
mailtrap_payverve_security_email = os.getenv('MAILTRAP_PAYVERVE_SECURITY_EMAIL')

fernet_key_one = os.getenv('FERNET_KEY_ONE')
fernet_key_two = os.getenv('FERNET_KEY_TWO')

algorithm = os.getenv('ALGORITHM', 'HS256')
access_token_time = int(os.getenv('ACCESS_TOKEN_TIME'))
access_secret_key = os.getenv('ACCESS_SECRET_KEY')
refresh_token_time = int(os.getenv('REFRESH_TOKEN_TIME'))
refresh_secret_key = os.getenv('REFRESH_SECRET_KEY')

paystack_secret_key = os.getenv('PAYSTACK_SECRET_KEY')
paystack_public_key = os.getenv('PAYSTACK_PUBLIC_KEY')
paystack_base_url = os.getenv('PAYSTACK_BASE_URL')
