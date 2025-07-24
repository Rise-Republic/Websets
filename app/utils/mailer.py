import smtplib
from email.message import EmailMessage

from app.config import settings


def send_email(to_address: str, subject: str, body: str) -> None:
    """Send an email via configured SMTP server."""
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.email_from
    msg["To"] = to_address
    msg.set_content(body)

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        server.starttls()
        if settings.smtp_username and settings.smtp_password:
            server.login(settings.smtp_username, settings.smtp_password)
        server.send_message(msg)


def send_password_reset_email(email: str, token: str) -> None:
    """Send password reset email with reset URL containing the token."""
    reset_url = f"{settings.frontend_url}/reset-password?token={token}"
    subject = "Password Reset Request"
    body = f"Click the following link to reset your password: {reset_url}"
    send_email(email, subject, body)
