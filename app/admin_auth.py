import os
import secrets
from typing import Any

from fastapi import Request
from fastapi.responses import RedirectResponse
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

SESSION_COOKIE = "lflux_admin_session"
SESSION_MAX_AGE = 60 * 60 * 24 * 7  # 7 days


def _serializer() -> URLSafeTimedSerializer:
    secret = os.getenv("ADMIN_SESSION_SECRET", "")
    if not secret:
        raise RuntimeError("ADMIN_SESSION_SECRET must be set")
    return URLSafeTimedSerializer(secret, salt="lflux-admin-session")


def get_admin_credentials() -> tuple[str, str]:
    username = os.getenv("ADMIN_USERNAME", "")
    password = os.getenv("ADMIN_PASSWORD", "")
    if not username or not password:
        raise RuntimeError("ADMIN_USERNAME and ADMIN_PASSWORD must be set")
    return username, password


def verify_admin_login(username: str, password: str) -> bool:
    expected_user, expected_pass = get_admin_credentials()
    user_ok = secrets.compare_digest(username, expected_user)
    pass_ok = secrets.compare_digest(password, expected_pass)
    return user_ok and pass_ok


def create_session_token(username: str) -> str:
    return _serializer().dumps({"username": username})


def read_session_token(token: str | None) -> str | None:
    if not token:
        return None
    try:
        payload: dict[str, Any] = _serializer().loads(token, max_age=SESSION_MAX_AGE)
    except (BadSignature, SignatureExpired):
        return None
    username = payload.get("username")
    if not isinstance(username, str) or not username:
        return None
    return username


def get_logged_in_admin(request: Request) -> str | None:
    return read_session_token(request.cookies.get(SESSION_COOKIE))


def set_admin_session(response: RedirectResponse, username: str) -> None:
    response.set_cookie(
        key=SESSION_COOKIE,
        value=create_session_token(username),
        max_age=SESSION_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=False,
    )


def clear_admin_session(response: RedirectResponse) -> None:
    response.delete_cookie(key=SESSION_COOKIE)


def require_admin(request: Request) -> str | RedirectResponse:
    username = get_logged_in_admin(request)
    if not username:
        return RedirectResponse(url="/admin/login", status_code=303)
    return username
