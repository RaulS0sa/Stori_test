import sys
import logging
import os
import smtplib
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from http import HTTPStatus

logger = logging.getLogger()
logger.setLevel(logging.INFO)

host_email = os.environ['SMTP_EMAIL']
host_password = os.environ['SMTP_PASSWORD']

def lambda_handler(event, context):
    """
    This function sends the email
    """
    try:
        message = event['Records'][0]['Sns']['Message']
        data = json.loads(message)
        logger.info(event)

        client_email = data.get('client')
        subject = data.get('subject')
        html = data.get('html')

        logger.info(f"sending email to {client_email}")

        smtp = smtplib.SMTP('smtp.zoho.com', port='587')
        smtp.ehlo()
        smtp.starttls()  # tell server we want to communicate with TLS encryption
        smtp.login(host_email, host_password)  # login to our email server

        msg = MIMEMultipart('alternative')
        msg['Subject'] = str(subject)

        msg.attach(MIMEText(html, 'html'))
        smtp.sendmail(host_email, client_email, msg.as_string())
        smtp.quit()

        return {
            "message": "sent",
            "status": HTTPStatus.OK
        }

    except Exception:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        raise
