import logging
import os

import httpx

logger = logging.getLogger(__name__)

SUBJECT = "[LFlux] 신규 상담 신청"
FROM_EMAIL = "LFlux <contact@lflux.co.kr>"
RESEND_API_URL = "https://api.resend.com/emails"


def _display(value: str | None) -> str:
    if value is None or not str(value).strip():
        return "미입력"
    return str(value).strip()


def _build_body(data: dict) -> str:
    return (
        "새로운 상담 신청이 접수되었습니다.\n\n"
        f"이름: {_display(data.get('name'))}\n"
        f"이메일: {_display(data.get('email'))}\n"
        f"연락처: {_display(data.get('phone'))}\n"
        f"업종: {_display(data.get('industry'))}\n"
        f"예산: {_display(data.get('budget'))}\n"
        f"관심 서비스: {_display(data.get('service_interest'))}\n\n"
        f"문의 내용:\n{_display(data.get('message'))}\n"
    )


def send_contact_notification(data: dict) -> None:
    api_key = os.getenv("RESEND_API_KEY", "").strip()
    if not api_key:
        logger.warning("RESEND_API_KEY not configured; skipping notification")
        return

    recipient = os.getenv("CONTACT_RECEIVER_EMAIL", "").strip()
    if not recipient:
        logger.warning("CONTACT_RECEIVER_EMAIL not configured; skipping notification")
        return

    payload = {
        "from": FROM_EMAIL,
        "to": [recipient],
        "subject": SUBJECT,
        "text": _build_body(data),
    }

    response = httpx.post(
        RESEND_API_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=30.0,
    )
    response.raise_for_status()

    logger.info(
        "Resend notification sent to %s for contact: %s",
        recipient,
        data.get("email"),
    )
