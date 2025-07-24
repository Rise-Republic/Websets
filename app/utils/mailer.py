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


def send_password_reset(to_address: str, reset_token: str) -> None:
    """Send a password reset email with a reset token link."""
    subject = "Password Reset Request"
    reset_url = f"{settings.frontend_url}/reset-password?token={reset_token}"
    body = f"""Hello,

You have requested to reset your password for your Websets account.

Please use the link below to reset your password:
{reset_url}

This link will expire in 30 minutes.

If you did not request this password reset, please ignore this email.

Best regards,
The Websets Team
"""
    
    send_email(to_address=to_address, subject=subject, body=body)
