"""
src/utilities/mailtrap_helper.py
This module contains a helper class for sending emails using Mailtrap.
It provides a method to send emails with specified recipients, subject, status_message, and optional attachments.
"""

import requests

import config


class MailtrapHelper:
    """ A helper class for sending emails using Mailtrap """

    @staticmethod
    def mailtrap_email_sender(sender_name: str, sender_email: str, endpoint: str, receipient: list, subject: str, mail_status_message, attachments: list = None):
        """ This method sends an email using Mailtrap API."""

        try:

            url = f"{config.mailtrap_base_url}{endpoint}"
            print("MAILTRAP URL:", url)
            print("MAILTRAP RESPONSE:", response.status_code, response.text)

            payload = {
                "from": {
                    "name": sender_name,
                    "email": sender_email
                },
                "to": receipient,
                "reply_to": {
                    "name": config.mailtrap_payverve_helpdesk_name,
                    "email": config.mailtrap_payverve_helpdesk_email
                },
                "subject": subject,
                "html": mail_status_message,
                "attachments": attachments,
            }
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Api-Token': config.mailtrap_api_key
            }

            response = requests.request(
                "POST", url, headers=headers, json=payload)

            return response

        except Exception as e:
            return {
                'code': 500,
                'status_message': 'server error',
                'message': f'an error occurred: {str(e)}'
            }
