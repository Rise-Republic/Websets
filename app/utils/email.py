import os
import smtplib
from email.message import EmailMessage


def send_password_reset(email: str, token: str) -> None:
    """Send password reset email with token link."""
    smtp_host = os.getenv("SMTP_HOST", "localhost")
    smtp_port = int(os.getenv("SMTP_PORT", "25"))
    smtp_user = os.getenv("SMTP_USERNAME")
    smtp_pass = os.getenv("SMTP_PASSWORD")
    from_addr = os.getenv("EMAIL_FROM", "no-reply@example.com")
    reset_url_base = os.getenv("PASSWORD_RESET_URL", "http://localhost")

    msg = EmailMessage()
    msg["Subject"] = "Password Reset"
    msg["From"] = from_addr
    msg["To"] = email
    reset_link = f"{reset_url_base}?token={token}"
    msg.set_content(f"Use this link to reset your password: {reset_link}")

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        if smtp_user and smtp_pass:
            server.starttls()
            server.login(smtp_user, smtp_pass)
        server.send_message(msg)
