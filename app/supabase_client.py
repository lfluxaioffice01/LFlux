"""
Supabase PostgREST helpers.

If the inquiries table has no status column yet, run in Supabase SQL Editor:

    alter table inquiries add column if not exists status text default 'new';

Portfolio table (run once if missing):

    create table if not exists portfolio (
        id bigint generated always as identity primary key,
        title text not null,
        description text,
        image_url text,
        project_url text,
        is_visible boolean default true,
        created_at timestamptz default now()
    );
"""

import os
from datetime import date, datetime, timezone
from functools import lru_cache
from typing import Any

from postgrest import SyncPostgrestClient
from postgrest.exceptions import APIError

VALID_INQUIRY_STATUSES = ("new", "checked", "done")


@lru_cache
def get_postgrest() -> SyncPostgrestClient:
    """PostgREST client using server-side Supabase service key."""
    url = os.getenv("SUPABASE_URL", "").rstrip("/")
    key = os.getenv("SUPABASE_SERVICE_KEY", "")

    if not url or not key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")

    return SyncPostgrestClient(
        f"{url}/rest/v1",
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
        },
    )


def insert_inquiry(data: dict) -> None:
    client = get_postgrest()
    row = {**data, "status": data.get("status") or "new"}
    try:
        client.from_("inquiries").insert(row).execute()
    except APIError as exc:
        raise RuntimeError(exc.message or "Supabase insert failed") from exc


def get_inquiries(limit: int | None = None) -> list[dict[str, Any]]:
    query = (
        get_postgrest()
        .from_("inquiries")
        .select("*")
        .order("created_at", desc=True)
    )
    if limit is not None:
        query = query.limit(limit)
    response = query.execute()
    return response.data or []


def get_inquiry(inquiry_id: int) -> dict[str, Any] | None:
    client = get_postgrest()
    response = (
        client.from_("inquiries")
        .select("*")
        .eq("id", inquiry_id)
        .limit(1)
        .execute()
    )

    if not response.data:
        return None

    return response.data[0]


def update_inquiry_status(inquiry_id: int, status: str) -> dict[str, Any] | None:
    if status not in VALID_INQUIRY_STATUSES:
        raise ValueError(f"Invalid status: {status}")

    response = (
        get_postgrest()
        .from_("inquiries")
        .update({"status": status})
        .eq("id", inquiry_id)
        .execute()
    )
    rows = response.data or []
    return rows[0] if rows else None


def _parse_created_date(created_at: str | None) -> date | None:
    if not created_at:
        return None
    try:
        normalized = created_at.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized).date()
    except ValueError:
        return None


def get_inquiry_stats() -> dict[str, int]:
    inquiries = get_inquiries()
    today = datetime.now(timezone.utc).date()

    total = len(inquiries)
    today_count = sum(
        1 for row in inquiries if _parse_created_date(row.get("created_at")) == today
    )
    new_count = sum(1 for row in inquiries if (row.get("status") or "new") == "new")
    completed_count = sum(1 for row in inquiries if row.get("status") == "done")

    return {
        "total": total,
        "today": today_count,
        "new": new_count,
        "completed": completed_count,
    }


def get_portfolio() -> list[dict[str, Any]]:
    response = (
        get_postgrest()
        .from_("portfolio")
        .select("*")
        .order("id", desc=True)
        .execute()
    )
    return response.data or []


def get_visible_portfolio() -> list[dict[str, Any]]:
    response = (
        get_postgrest()
        .from_("portfolio")
        .select("*")
        .eq("is_visible", True)
        .order("id", desc=True)
        .execute()
    )
    return response.data or []


def get_portfolio_item(item_id: int) -> dict[str, Any] | None:
    client = get_postgrest()
    response = (
        client.from_("portfolio")
        .select("*")
        .eq("id", item_id)
        .limit(1)
        .execute()
    )

    if not response.data:
        return None

    return response.data[0]


def create_portfolio_item(data: dict[str, Any]) -> dict[str, Any] | None:
    client = get_postgrest()
    try:
        response = client.from_("portfolio").insert(data).execute()
    except APIError as exc:
        raise RuntimeError(exc.message or "Portfolio insert failed") from exc
    rows = response.data or []
    return rows[0] if rows else None


def update_portfolio_item(item_id: int, data: dict[str, Any]) -> dict[str, Any] | None:
    client = get_postgrest()
    try:
        response = (
            client.from_("portfolio")
            .update(data)
            .eq("id", item_id)
            .execute()
        )
    except APIError as exc:
        raise RuntimeError(exc.message or "Portfolio update failed") from exc
    rows = response.data or []
    return rows[0] if rows else None


def delete_portfolio_item(item_id: int) -> None:
    client = get_postgrest()
    try:
        client.from_("portfolio").delete().eq("id", item_id).execute()
    except APIError as exc:
        raise RuntimeError(exc.message or "Portfolio delete failed") from exc