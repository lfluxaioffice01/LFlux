from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

CONTACT_PAYLOAD = {
    "name": "홍길동",
    "email": "test@example.com",
    "phone": "010-1234-5678",
    "industry": "학원",
    "budget": "100만원 ~ 300만원",
    "service_interest": "홈페이지 제작, AI 자동화",
    "message": "상담 요청합니다.",
}


@patch("app.main.send_contact_notification")
@patch("app.main.insert_inquiry")
def test_contact_success(mock_insert: MagicMock, mock_email: MagicMock) -> None:
    response = client.post("/contact", json=CONTACT_PAYLOAD)

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "상담 신청이 완료되었습니다."
    mock_insert.assert_called_once_with(CONTACT_PAYLOAD)
    mock_email.assert_called_once_with(CONTACT_PAYLOAD)


@patch("app.main.send_contact_notification", side_effect=Exception("SMTP failed"))
@patch("app.main.insert_inquiry")
def test_contact_email_failure_still_succeeds(
    mock_insert: MagicMock, mock_email: MagicMock
) -> None:
    response = client.post("/contact", json=CONTACT_PAYLOAD)

    assert response.status_code == 200
    assert response.json()["success"] is True
    mock_insert.assert_called_once()
    mock_email.assert_called_once()


@patch("app.main.send_contact_notification")
@patch("app.main.insert_inquiry")
def test_contact_supabase_error(mock_insert: MagicMock, mock_email: MagicMock) -> None:
    mock_insert.side_effect = RuntimeError("db error")

    response = client.post("/contact", json=CONTACT_PAYLOAD)

    assert response.status_code == 500
    body = response.json()
    assert body["success"] is False
    assert body["error"] == "상담 신청 중 오류가 발생했습니다."
    assert "db error" not in body["error"]
    assert "SUPABASE" not in response.text
    mock_email.assert_not_called()
