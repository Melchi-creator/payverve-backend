"""Defines the email server."""

from mailersend import emails

from .. import config


class EmailHandler:
    default_sender = config.mail_default_sender
    api_key = config.mail_api_key
    mail_from = {
            "name": "PayVerve",
            "email": default_sender
        }
    
    def sendMail(self, recipient='', subject='', plainText='', template=None):
        """Method for sending mail to a single address"""
        # May have to refactor to take in recipients as User object instead of email string
        mailer = emails.NewEmail(mailersend_api_key=self.api_key)
        mail_body = {}
        
        mail_from = self.mail_from
        reply_to = mail_from
        
        mailer.set_mail_from(mail_from, mail_body)
        mailer.set_reply_to(reply_to, mail_body)
        mailer.set_mail_to([{'email': recipient}], mail_body)
        mailer.set_subject(subject, mail_body)
        mailer.set_html_content(template, mail_body)
        mailer.set_plaintext_content(plainText, mail_body)
        
        res = mailer.send(message=mail_body)
        return res


    def sendBulkMail(self, recipients=[], subject='', plainText='', template=None):
        """Method for sending bulk mails to multiple addresses."""
        # May have to refactor to take in recipients as list of User object instead of email string
        mailer = emails.NewEmail(mailersend_api_key=self.api_key)
        mail_list = [
            {
            "from": self.mail_from,
            "to": [{'email': recipient}],
            "subject": subject,
            "text": plainText,
            "html": template,
        } for recipient in recipients]


    def bulkStatus(self, id):
        """Checks status of sent bulk mails"""
        mailer = emails.NewEmail(self.api_key)
        return mailer.get_bulk_status_by_id(id)
