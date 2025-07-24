import smtplib
from email.mime.text import MIMEText

from app.config import settings


def send_email(to_address: str, subject: str, body: str) -> None:
    """Send a plain text email using the configured SMTP server."""
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = settings.email_from
    msg["To"] = to_address

    with smtplib.SMTP(settings.smtp_host, int(settings.smtp_port)) as server:
        if settings.smtp_username and settings.smtp_password:
            server.login(settings.smtp_username, settings.smtp_password)
        server.send_message(msg)
