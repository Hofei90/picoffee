import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def email_inhalt_erstellen(text):
    html = f"""
    <html>
    <body>
    {text}
    </body>
    </html>
    """
    return MIMEText(html, "html")


def email_versenden(text, mail_config):
    sender = mail_config["sender_email"]
    receiver = mail_config["receiver_email"]
    message = MIMEMultipart("alternative")
    message["Subject"] = "Backupkontrolle"
    message["From"] = sender
    message["To"] = receiver
    message.attach(email_inhalt_erstellen(text))
    with smtplib.SMTP(
        mail_config["smtp_server"], mail_config["port"]
    ) as server:
        server.sendmail(sender, receiver, message.as_string())