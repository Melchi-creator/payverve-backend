import firebase_admin
from accounts.models import User
from django.conf import settings
from firebase_admin import auth, credentials
from rest_framework import authentication

from .exceptions import NoAuthToken, InvalidAuthToken, FirebaseError, EmailVerification

# Firebase Admin SDK credentials

try:
    # cred = credentials.Certificate({
    #     "type": settings.FIREBASE_ACCOUNT_TYPE,
    #     "project_id": settings.FIREBASE_PROJECT_ID,
    #     "private_key_id": settings.FIREBASE_PRIVATE_KEY_ID,
    #     "private_key": settings.FIREBASE_PRIVATE_KEY.replace('\\n', '\n'),
    #     "client_email": settings.FIREBASE_CLIENT_EMAIL,
    #     "client_id": settings.FIREBASE_CLIENT_ID,
    #     "auth_uri": settings.FIREBASE_AUTH_URI,
    #     "token_uri": settings.FIREBASE_TOKEN_URI,
    #     "auth_provider_x509_cert_url": settings.FIREBASE_AUTH_PROVIDER_X509_CERT_URL,
    #     "client_x509_cert_url": settings.FIREBASE_CLIENT_X509_CERT_URL
    # })
    cred = credentials.Certificate(settings.FIREBASE_CRED_FILE)
    default_app = firebase_admin.initialize_app(cred)
except Exception as ex:
    print(ex.__cause__)
    raise FirebaseError(
        f"Firebase Admin SDK credentials not found. "
        "Please add the path to the credentials file to "
        "the FIREBASE_ADMIN_SDK_CREDENTIALS_PATH environment variable. \n"
        "Caused by :: Exception :: ", ex.__cause__)


class FirebaseAuthentication(authentication.BaseAuthentication):
    """
    Firebase Authentication class.

    This class is used to authenticate users using Firebase.

    Attributes:
    - `keyword` (str): The keyword used to authenticate users.

    Methods:
    - `authenticate`: Authenticate the user using Firebase.
    - `get_user`: Get the user associated with the given Firebase token.

    """
    keyword = 'Bearer'

    def authenticate(self, request):
        """
        Authenticate the user using Firebase.

        Args:
        - `request` (Request): The request object.

        Returns:
        - tuple: A tuple containing the user and the token.

        """
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header:
            raise NoAuthToken("No authentication token provided.")
        id_token = auth_header.split(' ').pop()
        decoded_token = None
        try:
            decoded_token = auth.verify_id_token(id_token)
        except Exception:
            raise InvalidAuthToken("Invalid authentication token provided.")
        if not id_token or not decoded_token:
            return None

        email_verified = decoded_token.get('email_verified')
        if not email_verified:
            raise EmailVerification("Email not verified. please verify your email address.")

        try:
            uid = decoded_token.get('uid')
        except Exception:
            raise FirebaseError("The user proivded with auth token is not a firebase user. it has no firebase uid.")

        try:
            user = User.objects.get(firebase_uid=uid)
        except User.DoesNotExist:
            raise FirebaseError("The user proivded with auth token is not a firebase user. it has no firebase uid.")
        return user, None
