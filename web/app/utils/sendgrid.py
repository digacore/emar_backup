import os
import sendgrid
from flask import current_app

from sendgrid.helpers.mail import Mail, Content

class SendGridClient(object):
    def __init__(
            self,
            sendgrid_api_key):
        self._sg = sendgrid.SendGridAPIClient(api_key=sendgrid_api_key)

    def init_app(self, application, *args, **kwargs):
        super(SendGridClient, self).__init__(*args, **kwargs)

    @property
    def name(self):
        return 'sendgrid'

    def get_name(self):
        return self.name

    def send_email(self,
                   from_email,
                   to_addresses,
                   subject,
                   body,
                   html_body='',
                   reply_to_address=None):

        mail = Mail()
        mail.from_email = from_email
        mail.subject = subject
        plain_content = Content('text/plain', body)
        mail.add_content(plain_content)
        if html_body:
            html_content = Content('text/html', html_body)
            mail.add_content(html_content)
        mail.add_to(to_addresses)

        if isinstance(reply_to_address, str):
            mail.reply_to = reply_to_address
        print(mail.get())
        response = self._sg.client.mail.send.post(request_body=mail.get())
        
        print(response.status_code)
        print(response.headers)
        print(response.body)
        return response.headers['X-Message-Id']
