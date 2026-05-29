import os
from unittest.mock import MagicMock, patch

from app.gmail_notify import _get_recipient, send_contact_notification


def test_get_recipient_uses_contact_receiver_email() -> None:
    with patch.dict(
        os.environ,
        {"CONTACT_RECEIVER_EMAIL": "notify@example.com", "GMAIL_USER": "sender@gmail.com"},
        clear=False,
    ):
        assert _get_recipient("sender@gmail.com") == "notify@example.com"


def test_get_recipient_falls_back_to_gmail_user() -> None:
    with patch.dict(os.environ, {"CONTACT_RECEIVER_EMAIL": ""}, clear=False):
        assert _get_recipient("sender@gmail.com") == "sender@gmail.com"


@patch("app.gmail_notify.smtplib.SMTP")
def test_send_uses_receiver_email(mock_smtp: MagicMock) -> None:
    mock_server = MagicMock()
    mock_smtp.return_value.__enter__.return_value = mock_server

    with patch.dict(
        os.environ,
        {
            "GMAIL_USER": "sender@gmail.com",
            "GMAIL_APP_PASSWORD": "app pass word",
            "CONTACT_RECEIVER_EMAIL": "receiver@example.com",
        },
        clear=False,
    ):
        send_contact_notification({"name": "홍길동", "email": "user@example.com", "message": "hi"})

    mock_server.login.assert_called_once_with("sender@gmail.com", "apppassword")
    mock_server.sendmail.assert_called_once_with(
        "sender@gmail.com",
        ["receiver@example.com"],
        mock_server.sendmail.call_args[0][2],
    )
