import importlib.util
import os
import pytest


@pytest.mark.unit
def test_send_email_sends_message(mocker, mock_settings):
    mock_smtp = mocker.patch("smtplib.SMTP")

    spec = importlib.util.spec_from_file_location(
        "mailer", os.path.join("app", "utils", "mailer.py")
    )
    mailer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mailer)
    mailer.settings.smtp_host = "smtp.test"
    mailer.settings.smtp_port = 25
    mailer.settings.smtp_username = "user"
    mailer.settings.smtp_password = "pass"
    mailer.settings.email_from = "from@example.com"

    mailer.send_email("to@example.com", "Subject", "Body")

    mock_smtp.assert_called_with("smtp.test", 25)
    instance = mock_smtp.return_value.__enter__.return_value
    instance.login.assert_called_with("user", "pass")
    instance.send_message.assert_called_once()
