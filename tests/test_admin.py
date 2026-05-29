import os
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.admin_auth import create_session_token
from app.main import app

client = TestClient(app)

ADMIN_ENV = {
    "ADMIN_USERNAME": "admin",
    "ADMIN_PASSWORD": "secret-pass",
    "ADMIN_SESSION_SECRET": "test-session-secret-key-32chars!!",
}


def _auth_cookie() -> dict[str, str]:
    token = create_session_token("admin")
    return {"lflux_admin_session": token}


@patch.dict(os.environ, ADMIN_ENV, clear=False)
def test_admin_login_page() -> None:
    response = client.get("/admin/login")
    assert response.status_code == 200
    assert "관리자 로그인" in response.text


@patch.dict(os.environ, ADMIN_ENV, clear=False)
def test_admin_login_failure() -> None:
    response = client.post(
        "/admin/login",
        data={"username": "admin", "password": "wrong"},
    )
    assert response.status_code == 401
    assert "올바르지 않습니다" in response.text


@patch.dict(os.environ, ADMIN_ENV, clear=False)
def test_admin_login_success_redirects() -> None:
    response = client.post(
        "/admin/login",
        data={"username": "admin", "password": "secret-pass"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/admin"
    assert "lflux_admin_session" in response.cookies


@patch.dict(os.environ, ADMIN_ENV, clear=False)
def test_admin_requires_login() -> None:
    with TestClient(app) as isolated_client:
        response = isolated_client.get("/admin", follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"] == "/admin/login"


@patch("app.admin_routes.get_inquiry_stats")
@patch("app.admin_routes.get_inquiries")
@patch.dict(os.environ, ADMIN_ENV, clear=False)
def test_admin_dashboard(
    mock_get_inquiries: MagicMock,
    mock_get_stats: MagicMock,
) -> None:
    mock_get_stats.return_value = {"total": 2, "today": 1, "new": 1, "completed": 0}
    mock_get_inquiries.return_value = [
        {
            "id": 1,
            "name": "홍길동",
            "phone": "010",
            "status": "new",
            "created_at": "2026-05-29T10:00:00+00:00",
        }
    ]

    response = client.get("/admin", cookies=_auth_cookie())
    assert response.status_code == 200
    assert "대시보드" in response.text
    assert "전체 문의" in response.text


@patch("app.admin_routes.update_inquiry_status")
@patch.dict(os.environ, ADMIN_ENV, clear=False)
def test_admin_update_status(mock_update: MagicMock) -> None:
    response = client.post(
        "/admin/inquiries/1/status",
        data={"status": "done"},
        cookies=_auth_cookie(),
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/admin/inquiries/1"
    mock_update.assert_called_once_with(1, "done")


@patch("app.admin_routes.get_portfolio")
@patch.dict(os.environ, ADMIN_ENV, clear=False)
def test_admin_portfolio_list(mock_get_items: MagicMock) -> None:
    mock_get_items.return_value = [
        {"id": 1, "title": "테스트", "is_visible": True, "project_url": None}
    ]

    response = client.get("/admin/portfolio", cookies=_auth_cookie())
    assert response.status_code == 200
    assert "포트폴리오" in response.text
    assert "테스트" in response.text


@patch("app.admin_routes.create_portfolio_item")
@patch.dict(os.environ, ADMIN_ENV, clear=False)
def test_admin_portfolio_create(mock_create: MagicMock) -> None:
    response = client.post(
        "/admin/portfolio/new",
        data={
            "title": "새 프로젝트",
            "description": "설명",
            "image_url": "",
            "project_url": "",
            "is_visible": "on",
        },
        cookies=_auth_cookie(),
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/admin/portfolio"
    mock_create.assert_called_once()
