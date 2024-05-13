import smtplib
import os, sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dtraia_api.utils.configs import get_email_creds

BASE_TEMPLATES_ROUTE = os.environ["TEMPLATES_ROUTE"] if os.environ.get("TEMPLATES_ROUTE") else "/home/ralvarez22/Documentos/dtraia/dtraia_api/templates"

def send_message(rcv, sender = "dtraia@restore.com", subject = "Servicio de restablecimiento de contraseña", template = "password_recovery.html", template_params = {}):
    user_email, pwd_email = get_email_creds()
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    smtp_username = user_email
    smtp_password = pwd_email

    from_email = sender
    to_email = rcv
    
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = rcv
    
    body = open(os.path.join(BASE_TEMPLATES_ROUTE, template), "r", encoding="utf8").read().format_map(template_params)

    msg.attach(MIMEText(body, 'html'))


    with smtplib.SMTP(smtp_server, smtp_port) as smtp:
        smtp.starttls()
        smtp.login(smtp_username, smtp_password)
        smtp.sendmail(from_email, to_email, msg.as_string())