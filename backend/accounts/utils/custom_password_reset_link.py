from accounts.firebase_auth.authentication import auth as firebase_admin_auth
from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.mail import send_mail, get_connection

# celery logger
logger = get_task_logger(__name__)


# TODO: read on celery


# create custom password reset link using celery background task
@shared_task()
def generate_custom_password_link_from_firebase(user_email, display_name):
    action_code_settings = firebase_admin_auth.ActionCodeSettings(
        url='https://www.yourwebsite.example/',
        handle_code_in_app=True,
    )
    custom_verification_link = firebase_admin_auth.generate_password_reset_link(user_email, action_code_settings)
    subject = 'Reset your password'
    message = f'Hello {display_name},\n\nPlease reset your password by clicking on the link below:\n\n{custom_verification_link}\n\nThanks,\nYour website team'
    send_email(subject, message, user_email)


# send email using django send_mail
def send_email(subject, message, user_email):
    with get_connection(
            host=settings.EMAIL_HOST,
            port=settings.EMAIL_PORT,
            username=settings.EMAIL_HOST_USER,
            password=settings.EMAIL_HOST_PASSWORD,
            use_tls=settings.EMAIL_USE_TLS
    ) as connection:
        from_email = settings.EMAIL_HOST_USER
        recipient = user_email
        send_mail(subject, message, from_email, [recipient], fail_silently=False, connection=connection)
