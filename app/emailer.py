from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To
from .settings import settings

import urllib3
from python_http_client import client


import os
import certifi

os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()
os.environ["SSL_CERT_FILE"] = certifi.where()



# Disable SSL verification warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class UnsafeSendGridAPIClient(SendGridAPIClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Replace the pool manager with one that skips certificate validation
        if self.client and hasattr(self.client, '_request'):
            self.client._request._http = urllib3.PoolManager(cert_reqs='CERT_NONE')

class Emailer:
    def __init__(self):
        if not settings.SENDGRID_API_KEY:
            raise RuntimeError("SENDGRID_API_KEY is not set")
        if not settings.SENDGRID_TEMPLATE_ID:
            raise RuntimeError("SENDGRID_TEMPLATE_ID is not set")
        if not settings.SENDGRID_FROM_EMAIL:
            raise RuntimeError("SENDGRID_FROM_EMAIL is not set")

        # Use our unsafe client that skips SSL cert check
        self.client = UnsafeSendGridAPIClient(settings.SENDGRID_API_KEY)

    def send(self, to_email: str, dynamic_template_data: dict) -> str:
        msg = Mail(
            from_email=Email(
                settings.SENDGRID_FROM_EMAIL,
                settings.SENDGRID_FROM_NAME,
            ),
            to_emails=To(to_email),
        )
        msg.template_id = settings.SENDGRID_TEMPLATE_ID
        msg.dynamic_template_data = dynamic_template_data

        resp = self.client.send(msg)
        return f"{resp.status_code}"


emailer = Emailer()
