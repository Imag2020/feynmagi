import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from email.utils import formatdate

import json
import pkg_resources

# Charger la configuration SMTP
def load_config():
    try:
        file_conf = pkg_resources.resource_filename('feynmagi', 'data/config_mail.json')
        with open(file_conf, 'r') as file:
            return json.load(file)
    except Exception as e:
        print(f"Error opening mail config json : {e}")
        return None
        
def send_email(to_email, subject, body, attachment=None):
    config = load_config()
    if config is None:
        return "Mail not sent, chack config json"
    
    message = MIMEMultipart()
    message['From'] = config['email_from']
    message['To'] = to_email
    message['Subject'] = subject
    message['Date'] = formatdate(localtime=True)

    # Corps du message
    part = MIMEText(body, 'html', 'utf-8')
    message.attach(part)

    # Pièce jointe (optionnelle)
    if attachment:
        with open(attachment, 'rb') as attachmentf:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachmentf.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="{attachment}"')
            message.attach(part)

    # Envoi de l'email
    try:
        server = smtplib.SMTP(config['smtp_server'], config['smtp_port'])
        server.ehlo()  # Commande de salutation à SMTP
        text = message.as_string()
        server.sendmail(message['From'], message['To'], message.as_string())
        server.quit()
        return "Email sent succefully"
    except Exception as e:
        return f"An error occured sending mail {e}"
