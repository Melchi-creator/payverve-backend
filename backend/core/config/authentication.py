import firebase_admin
from django.conf import settings
from django.contrib.auth.models import User
from firebase_admin import credentials, auth
from rest_framework.authentication import BaseAuthentication

from .exceptions import NoAuthToken, InvalidAuthToken, FirebaseError

# SETUP FIREBASE CREDENTIALS
cred = credentials.Certificate({
    "type": settings.FIREBASE_ACCOUNT_TYPE,
    "project_id": settings.FIREBASE_PROJECT_ID,
    "private_key_id": settings.FIREBASE_PRIVATE_KEY_ID,
    "private_key": settings.FIREBASE_PRIVATE_KEY.replace('\\n', '\n'),
    "client_email": settings.FIREBASE_CLIENT_EMAIL,
    "client_id": settings.FIREBASE_CLIENT_ID,
    "auth_uri": settings.FIREBASE_AUTH_URI,
    "token_uri": settings.FIREBASE_TOKEN_URI,
    "auth_provider_x509_cert_url": settings.FIREBASE_AUTH_PROVIDER_X509_CERT_URL,
    "client_x509_cert_url": settings.FIREBASE_CLIENT_X509_CERT_URL
})
default_app = firebase_admin.initialize_app(cred)


# FIREBASE AUTHENTICATION
class FirebaseAuthentication(BaseAuthentication):
    """override authenticate method and write our custom firebase authentication."""

    def authenticate(self, request):
        """Get the authorization Token, It raises exception when no authorization Token is given"""
        auth_header = request.META.get("HTTP_AUTHORIZATION")
        if not auth_header:
            raise NoAuthToken("No auth token provided")
        """Decoding the Token It raise exception when decode failed."""
        id_token = auth_header.split(" ").pop()
        decoded_token = None
        try:
            decoded_token = auth.verify_id_token(id_token)
        except Exception:
            raise InvalidAuthToken("Invalid auth token")
        """Return Nothing"""
        if not id_token or not decoded_token:
            return None
        """Get the uid of an user"""
        try:
            uid = decoded_token.get("uid")
        except Exception:
            raise FirebaseError()
        """Get or create the user"""
        user, created = User.objects.get_or_create(username=uid)
        return user, None


"""
    def post(self, request):
        email = request.POST.get("email")
        password = request.POST.get("password")

        user = auth.create_user_with_email_and_password(email, password)
        auth.send_email_verification(user['idToken'])

        django_user, _ = User.objects.get_or_create(email=email)
        # If you want to copy the password from firebase
        if not django_user.check_password(password):
            django_user.set_password(password)
            django_user.save()

        # Pass the token to the client to make authenticated requests
        token, _ = Token.objects.get_or_create(user=django_user))
        user['token'] = token.key
        return Response(user)  """
