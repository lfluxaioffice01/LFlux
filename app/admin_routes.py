from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.admin_auth import (
    clear_admin_session,
    get_logged_in_admin,
    require_admin,
    set_admin_session,
    verify_admin_login,
)
from app.supabase_client import (
    VALID_INQUIRY_STATUSES,
    create_portfolio_item,
    delete_portfolio_item,
    get_inquiries,
    get_inquiry,
    get_inquiry_stats,
    get_portfolio_item,
    get_portfolio,
    update_inquiry_status,
    update_portfolio_item,
)

router = APIRouter(tags=["admin"])

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

STATUS_LABELS = {
    "new": "신규",
    "checked": "확인됨",
    "done": "완료",
}


def _format_datetime(value: str | None) -> str:
    if not value:
        return "-"
    try:
        normalized = value.replace("Z", "+00:00")
        dt = datetime.fromisoformat(normalized)
        return dt.strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return value


def _enrich_inquiry(row: dict[str, Any]) -> dict[str, Any]:
    status = row.get("status") or "new"
    return {
        **row,
        "status": status,
        "status_label": STATUS_LABELS.get(status, status),
        "created_at_display": _format_datetime(row.get("created_at")),
    }


def _admin_context(request: Request, username: str, **extra: Any) -> dict[str, Any]:
    return {
        "request": request,
        "admin_user": username,
        "status_labels": STATUS_LABELS,
        **extra,
    }


@router.get("/admin/login", response_class=HTMLResponse, response_model=None, name="admin_login")
async def admin_login_page(
    request: Request,
    error: str | None = None,
):
    if get_logged_in_admin(request):
        return RedirectResponse(url="/admin", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="admin_login.html",
        context={"request": request, "error": error},
    )


@router.post("/admin/login", response_model=None)
async def admin_login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    if not verify_admin_login(username.strip(), password):
        return templates.TemplateResponse(
            request=request,
            name="admin_login.html",
            context={
                "request": request,
                "error": "아이디 또는 비밀번호가 올바르지 않습니다.",
            },
            status_code=401,
        )

    response = RedirectResponse(url="/admin", status_code=303)
    set_admin_session(response, username.strip())
    return response


@router.get("/admin/logout")
async def admin_logout() -> RedirectResponse:
    response = RedirectResponse(url="/admin/login", status_code=303)
    clear_admin_session(response)
    return response


@router.get("/admin", response_class=HTMLResponse, response_model=None, name="admin_dashboard")
async def admin_dashboard(request: Request):
    auth = require_admin(request)
    if isinstance(auth, RedirectResponse):
        return auth

    stats = get_inquiry_stats()
    recent = [_enrich_inquiry(row) for row in get_inquiries(limit=5)]

    return templates.TemplateResponse(
        request=request,
        name="admin_dashboard.html",
        context=_admin_context(request, auth, stats=stats, recent_inquiries=recent),
    )


@router.get("/admin/inquiries", response_class=HTMLResponse, response_model=None, name="admin_inquiries")
async def admin_inquiries_list(request: Request):
    auth = require_admin(request)
    if isinstance(auth, RedirectResponse):
        return auth

    inquiries = [_enrich_inquiry(row) for row in get_inquiries()]

    return templates.TemplateResponse(
        request=request,
        name="admin_inquiries.html",
        context=_admin_context(request, auth, inquiries=inquiries),
    )


@router.get("/admin/inquiries/{inquiry_id}", response_class=HTMLResponse, response_model=None)
async def admin_inquiry_detail(
    request: Request,
    inquiry_id: int,
):
    auth = require_admin(request)
    if isinstance(auth, RedirectResponse):
        return auth

    row = get_inquiry(inquiry_id)
    if not row:
        raise HTTPException(status_code=404, detail="문의를 찾을 수 없습니다.")

    inquiry = _enrich_inquiry(row)

    return templates.TemplateResponse(
        request=request,
        name="admin_inquiry_detail.html",
        context=_admin_context(request, auth, inquiry=inquiry),
    )


@router.post("/admin/inquiries/{inquiry_id}/status")
async def admin_inquiry_update_status(
    request: Request,
    inquiry_id: int,
    status: str = Form(...),
) -> RedirectResponse:
    auth = require_admin(request)
    if isinstance(auth, RedirectResponse):
        return auth

    if status in VALID_INQUIRY_STATUSES:
        update_inquiry_status(inquiry_id, status)

    return RedirectResponse(
        url=f"/admin/inquiries/{inquiry_id}",
        status_code=303,
    )


def _form_bool(value: str | None) -> bool:
    return value in ("on", "true", "1", "yes")


def _portfolio_form_data(
    title: str,
    description: str,
    image_url: str,
    project_url: str,
    is_visible: str | None,
) -> dict[str, Any]:
    return {
        "title": title.strip(),
        "description": description.strip() or None,
        "image_url": image_url.strip() or None,
        "project_url": project_url.strip() or None,
        "is_visible": _form_bool(is_visible),
    }


@router.get("/admin/portfolio", response_class=HTMLResponse, response_model=None)
async def admin_portfolio_list(request: Request):
    auth = require_admin(request)
    if isinstance(auth, RedirectResponse):
        return auth

    items = get_portfolio()

    return templates.TemplateResponse(
        request=request,
        name="admin_portfolio.html",
        context=_admin_context(request, auth, items=items),
    )


@router.get("/admin/portfolio/new", response_class=HTMLResponse, response_model=None)
async def admin_portfolio_new_form(request: Request):
    auth = require_admin(request)
    if isinstance(auth, RedirectResponse):
        return auth

    return templates.TemplateResponse(
        request=request,
        name="admin_portfolio_form.html",
        context=_admin_context(
            request,
            auth,
            item=None,
            form_title="포트폴리오 추가",
            form_action="/admin/portfolio/new",
        ),
    )


@router.post("/admin/portfolio/new", response_model=None)
async def admin_portfolio_create(
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
    image_url: str = Form(""),
    project_url: str = Form(""),
    is_visible: str | None = Form(None),
):
    auth = require_admin(request)
    if isinstance(auth, RedirectResponse):
        return auth

    if not title.strip():
        return templates.TemplateResponse(
            request=request,
            name="admin_portfolio_form.html",
            context=_admin_context(
                request,
                auth,
                item=None,
                form_title="포트폴리오 추가",
                form_action="/admin/portfolio/new",
                error="제목을 입력해 주세요.",
            ),
            status_code=400,
        )

    create_portfolio_item(
        _portfolio_form_data(title, description, image_url, project_url, is_visible)
    )
    return RedirectResponse(url="/admin/portfolio", status_code=303)


@router.get("/admin/portfolio/{item_id}/edit", response_class=HTMLResponse, response_model=None)
async def admin_portfolio_edit_form(request: Request, item_id: int):
    auth = require_admin(request)
    if isinstance(auth, RedirectResponse):
        return auth

    item = get_portfolio_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="포트폴리오 항목을 찾을 수 없습니다.")

    return templates.TemplateResponse(
        request=request,
        name="admin_portfolio_form.html",
        context=_admin_context(
            request,
            auth,
            item=item,
            form_title="포트폴리오 수정",
            form_action=f"/admin/portfolio/{item_id}/edit",
        ),
    )


@router.post("/admin/portfolio/{item_id}/edit", response_model=None)
async def admin_portfolio_update(
    request: Request,
    item_id: int,
    title: str = Form(...),
    description: str = Form(""),
    image_url: str = Form(""),
    project_url: str = Form(""),
    is_visible: str | None = Form(None),
):
    auth = require_admin(request)
    if isinstance(auth, RedirectResponse):
        return auth

    item = get_portfolio_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="포트폴리오 항목을 찾을 수 없습니다.")

    if not title.strip():
        return templates.TemplateResponse(
            request=request,
            name="admin_portfolio_form.html",
            context=_admin_context(
                request,
                auth,
                item=item,
                form_title="포트폴리오 수정",
                form_action=f"/admin/portfolio/{item_id}/edit",
                error="제목을 입력해 주세요.",
            ),
            status_code=400,
        )

    update_portfolio_item(
        item_id,
        _portfolio_form_data(title, description, image_url, project_url, is_visible),
    )
    return RedirectResponse(url="/admin/portfolio", status_code=303)


@router.post("/admin/portfolio/{item_id}/delete", response_model=None)
async def admin_portfolio_delete(request: Request, item_id: int):
    auth = require_admin(request)
    if isinstance(auth, RedirectResponse):
        return auth

    item = get_portfolio_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="포트폴리오 항목을 찾을 수 없습니다.")

    delete_portfolio_item(item_id)
    return RedirectResponse(url="/admin/portfolio", status_code=303)
