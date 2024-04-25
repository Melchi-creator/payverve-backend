from accounts.firebase_auth.authentication import auth as firebase_admin_auth
from django.conf import settings
from django.core.mail import send_mail, get_connection


# create custom email verification link
def generate_custom_email_from_firebase(user_email, display_name):
    action_code_settings = firebase_admin_auth.ActionCodeSettings(
        url='https://www.yourwebsite.example/',
        handle_code_in_app=True,
    )
    custom_verification_link = firebase_admin_auth.generate_email_verification_link(user_email, action_code_settings)
    # print(f'custom_verification_link: {custom_verification_link}')
    subject = 'Verify your email address'
    message = f'Hello {display_name},\n\nPlease verify your email address by clicking on the link below:\n\n{custom_verification_link}\n\nThanks,\nYour website team'
    send_email(subject, message, user_email)


# send email using django send_mail
def send_email(subject, message, user_email):
    with get_connection(
            host=settings.EMAIL_HOST,
            port=settings.EMAIL_PORT,
            username=settings.EMAIL_HOST_USER,
            password=settings.EMAIL_HOST_PASSWORD,
            use_tls=settings.EMAIL_USE_TLS,
            use_ssl=settings.EMAIL_USE_SSL
    ) as connection:
        from_email = settings.EMAIL_HOST_USER
        recipient = user_email
        send_mail(subject, message, from_email, [recipient], fail_silently=False, connection=connection)

    # from_email = settings.EMAIL_HOST_USER
    # recipient = user_email
    # send_mail(subject, message, from_email, [recipient], fail_silently=False)
