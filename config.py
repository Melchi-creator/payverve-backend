"""
config.py

Holds all variables configuration required for the app to successfully run
Fetch all variables from .env
"""

import json
import os

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()


# --- AWS Secrets Manager integration ---
def get_secret(secret_name="prod-payverve", region_name="af-south-1"):
    """Fetch a secret from AWS Secrets Manager and return as dict."""
    session = boto3.session.Session()
    client = session.client(
        service_name="secretsmanager",
        region_name=region_name,
    )
    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        raise e

    return json.loads(get_secret_value_response["SecretString"])


# Flag to determine whether to use AWS secrets
USE_AWS_SECRETS = True if os.getenv('ENV') is None else False
secrets = get_secret() if USE_AWS_SECRETS else {}


def get_config(key: str, default=None):
    """Helper to fetch config from AWS secrets first, then .env."""
    if USE_AWS_SECRETS and key in secrets:
        return secrets[key]
    return os.getenv(key, default)


env = get_config('ENV')
secret_key = get_config('SECRET_KEY')
debug = get_config('DEBUG')

app_host = get_config('APP_HOST')
app_port = get_config('APP_PORT')
app_root = get_config('APP_ROOT')
app_path = get_config('APP_PATH')

database_username = get_config('DB_USERNAME')
database_paswword = get_config('DB_PASSWORD')
database_host = get_config('DB_HOST')
database_port = get_config('DB_PORT')
database_name = get_config('DB_NAME')

database_uri = f"postgresql://{database_username}:{database_paswword}@{database_host}:{database_port}/{database_name}"
database_tracker = False

mobile_app_path = get_config('MOBILE_APP_PATH')

exchange_rate_api_url = get_config('EXCHANGERATE_API_URL')
exchange_rate_api_key = get_config('EXCHANGERATE_API_KEY')

mailtrap_base_url = get_config('MAILTRAP_BASE_URL')
mailtrap_api_key = get_config('MAILTRAP_API_KEY')
mailtrap_payverve_helpdesk_name = get_config('MAILTRAP_PAYVERVE_HELPDESK_NAME')
mailtrap_payverve_helpdesk_email = get_config('MAILTRAP_PAYVERVE_HELPDESK_EMAIL')
mailtrap_payverve_eva_name = get_config('MAILTRAP_PAYVERVE_EVA_NAME')
mailtrap_payverve_eva_email = get_config('MAILTRAP_PAYVERVE_EVA_EMAIL')
mailtrap_payverve_security_name = get_config('MAILTRAP_PAYVERVE_SECURITY_NAME')
mailtrap_payverve_security_email = get_config('MAILTRAP_PAYVERVE_SECURITY_EMAIL')

fernet_key_one = get_config('FERNET_KEY_ONE')
fernet_key_two = get_config('FERNET_KEY_TWO')

algorithm = get_config('ALGORITHM', 'HS256')
access_token_time = int(get_config('ACCESS_TOKEN_TIME'))
access_secret_key = get_config('ACCESS_SECRET_KEY')
refresh_token_time = int(get_config('REFRESH_TOKEN_TIME'))
refresh_secret_key = get_config('REFRESH_SECRET_KEY')

paystack_secret_key = get_config('PAYSTACK_SECRET_KEY')
paystack_public_key = get_config('PAYSTACK_PUBLIC_KEY')
paystack_base_url = get_config('PAYSTACK_BASE_URL')

low_fx_payvevrve_charge: float = float(get_config('LOW_FX_PAYVERVE_CHARGE'))
high_fx_payverve_charge: float = float(get_config('HIGH_FX_PAYVERVE_CHARGE'))

flutterwave_public_key = get_config('FLUTTERWAVE_PUBLIC_KEY')
flutterwave_secret_key = get_config('FLUTTERWAVE_SECRET_KEY')
flutterwave_encryption_key = get_config('FLUTTERWAVE_ENCRYPTION_KEY')
flutterwave_base_url = get_config('FLUTTERWAVE_BASE_URL')
flutterwave_secret_hash = get_config('FLUTTERWAVE_SECRET_HASH')

flutterwave_client_id = get_config('FLUTTERWAVE_CLIENT_ID')
flutterwave_file_encryption = get_config('FLUTTERWAVE_FILE_ENCRYPTION')
flutterwave_auth_url = get_config('FLUTTERWAVE_AUTH_URL')
