from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@patch("app.main.get_visible_portfolio", return_value=[])
def test_homepage(_mock_portfolio) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "비즈니스 자동화의 시작" in response.text
    assert "왜 LFlux인가?" in response.text
    assert "웹 제작, 온라인 홍보, AI 자동화를 한 번에 관리합니다." in response.text
    assert "프로젝트 사례" in response.text
    assert "Willow" not in response.text
    assert "Project Overseas" not in response.text
    assert "관심 서비스" in response.text
    assert "온라인 홍보 운영" in response.text
    assert "기타 문의" in response.text
    assert "김기범" in response.text
    assert "010-9155-6922" in response.text


@patch("app.main.get_visible_portfolio")
def test_homepage_loads_portfolio(mock_portfolio) -> None:
    mock_portfolio.return_value = [
        {
            "id": 1,
            "title": "테스트 프로젝트",
            "description": "설명",
            "image_url": None,
            "project_url": None,
            "is_visible": True,
        }
    ]
    response = client.get("/")
    assert response.status_code == 200
    assert "테스트 프로젝트" in response.text


@patch("app.main.get_visible_portfolio")
def test_homepage_portfolio_empty_state(mock_portfolio) -> None:
    mock_portfolio.return_value = []
    response = client.get("/")
    assert response.status_code == 200
    assert "등록된 프로젝트가 없습니다." in response.text
