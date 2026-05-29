import os
from unittest.mock import MagicMock, patch

import httpx

from app.email_notify import send_contact_notification


@patch("app.email_notify.httpx.post")
def test_send_contact_notification(mock_post: MagicMock) -> None:
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    with patch.dict(
        os.environ,
        {
            "RESEND_API_KEY": "re_test_key",
            "CONTACT_RECEIVER_EMAIL": "receiver@example.com",
        },
        clear=False,
    ):
        send_contact_notification(
            {
                "name": "홍길동",
                "email": "user@example.com",
                "phone": "010-1234-5678",
                "industry": "학원",
                "budget": "100만원",
                "service_interest": "홈페이지 제작",
                "message": "상담 요청",
            }
        )

    mock_post.assert_called_once()
    call_kwargs = mock_post.call_args.kwargs
    assert call_kwargs["headers"]["Authorization"] == "Bearer re_test_key"
    assert call_kwargs["headers"]["Content-Type"] == "application/json"
    assert call_kwargs["json"]["from"] == "onboarding@resend.dev"
    assert call_kwargs["json"]["to"] == ["receiver@example.com"]
    assert call_kwargs["json"]["subject"] == "[LFlux] 신규 상담 신청"
    assert "홍길동" in call_kwargs["json"]["text"]
    assert "상담 요청" in call_kwargs["json"]["text"]


@patch("app.email_notify.httpx.post")
def test_send_skips_when_api_key_missing(mock_post: MagicMock) -> None:
    with patch.dict(os.environ, {"RESEND_API_KEY": ""}, clear=False):
        send_contact_notification({"name": "홍길동", "email": "user@example.com", "message": "hi"})

    mock_post.assert_not_called()


@patch("app.email_notify.httpx.post")
def test_send_raises_on_api_error(mock_post: MagicMock) -> None:
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "error",
        request=MagicMock(),
        response=MagicMock(status_code=422),
    )
    mock_post.return_value = mock_response

    with patch.dict(
        os.environ,
        {
            "RESEND_API_KEY": "re_test_key",
            "CONTACT_RECEIVER_EMAIL": "receiver@example.com",
        },
        clear=False,
    ):
        try:
            send_contact_notification({"name": "홍길동", "email": "user@example.com", "message": "hi"})
            raised = False
        except httpx.HTTPStatusError:
            raised = True

    assert raised
