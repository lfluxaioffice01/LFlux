import base64
import json
import logging
import os
import traceback
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from postgrest.exceptions import APIError

from app.admin_routes import router as admin_router
from app.email_notify import send_contact_notification
from app.schemas import ContactIn
from app.supabase_client import get_postgrest, get_visible_portfolio, insert_inquiry

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent

for env_path in (BASE_DIR / ".env", BASE_DIR / "templates" / ".env"):
    if env_path.exists():
        load_dotenv(env_path)

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="LFlux", version="0.1.0")

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

app.include_router(admin_router)

CONTACT_ERROR_MESSAGE = "상담 신청 중 오류가 발생했습니다."
CONTACT_SUCCESS_MESSAGE = "상담 신청이 완료되었습니다."


@app.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    try:
        portfolio = get_visible_portfolio()
    except Exception as exc:
        logger.exception("Failed to load portfolio items: %s", exc)
        portfolio = []

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"request": request, "portfolio": portfolio},
    )


@app.post("/contact")
async def submit_contact(payload: ContactIn) -> JSONResponse:
    data = payload.model_dump()

    try:
        insert_inquiry(data)
    except Exception as exc:
        logger.exception("Contact form submission failed: %s", exc)
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": CONTACT_ERROR_MESSAGE},
        )

    try:
        send_contact_notification(data)
    except Exception as exc:
        logger.exception("Email notification failed: %s", exc)

    return JSONResponse(
        content={"success": True, "message": CONTACT_SUCCESS_MESSAGE},
    )


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


def _key_prefix(key: str | None) -> str | None:
    if not key:
        return None
    return key[:20]


def _auth_role_from_key(key: str) -> str | None:
    if key.startswith("eyJ"):
        try:
            payload_segment = key.split(".")[1]
            padding = "=" * (-len(payload_segment) % 4)
            payload = json.loads(base64.urlsafe_b64decode(payload_segment + padding))
            role = payload.get("role")
            return str(role) if role is not None else None
        except (IndexError, json.JSONDecodeError, ValueError):
            return None
    if key.startswith("sb_publishable_"):
        return "anon (inferred from publishable key)"
    if key.startswith("sb_secret_"):
        return "service_role (inferred from secret key)"
    return None


@app.get("/debug-supabase")
def debug_supabase() -> dict[str, Any]:
    """Temporary endpoint — remove before production deploy."""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")

    result: dict[str, Any] = {
        "supabase_url_loaded": bool(supabase_url),
        "supabase_anon_key_loaded": bool(supabase_key),
        "supabase_anon_key_prefix": _key_prefix(supabase_key),
        "auth_role": _auth_role_from_key(supabase_key) if supabase_key else None,
        "insert_test": None,
    }

    if not supabase_url or not supabase_key:
        result["insert_test"] = {
            "attempted": False,
            "reason": "Missing SUPABASE_URL or SUPABASE_ANON_KEY",
        }
        return result

    debug_row = {"name": "debug", "message": "debug"}
    try:
        get_postgrest().from_("inquiries").insert(debug_row).execute()
        result["insert_test"] = {
            "attempted": True,
            "success": True,
            "payload": debug_row,
        }
    except APIError as exc:
        raw_error = getattr(exc, "_raw_error", None)
        if raw_error is None and exc.args and isinstance(exc.args[0], dict):
            raw_error = exc.args[0]
        result["insert_test"] = {
            "attempted": True,
            "success": False,
            "payload": debug_row,
            "supabase_error": raw_error,
            "error_code": exc.code,
            "error_message": exc.message,
            "error_hint": exc.hint,
            "error_details": exc.details,
        }
    except Exception as exc:
        result["insert_test"] = {
            "attempted": True,
            "success": False,
            "payload": debug_row,
            "error_type": type(exc).__name__,
            "error_message": str(exc),
        }

    return result
