import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)

SUBJECT = "[LFlux] 신규 상담 신청"
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587


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


def _get_recipient(gmail_user: str) -> str:
    receiver = os.getenv("CONTACT_RECEIVER_EMAIL", "").strip()
    return receiver if receiver else gmail_user


def send_contact_notification(data: dict) -> None:
    gmail_user = os.getenv("GMAIL_USER")
    gmail_password = os.getenv("GMAIL_APP_PASSWORD", "").replace(" ", "")

    if not gmail_user or not gmail_password:
        logger.warning("Gmail credentials not configured; skipping notification")
        return

    recipient = _get_recipient(gmail_user)

    message = MIMEMultipart()
    message["From"] = gmail_user
    message["To"] = recipient
    message["Subject"] = SUBJECT
    message.attach(MIMEText(_build_body(data), "plain", "utf-8"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
        server.starttls()
        server.login(gmail_user, gmail_password)
        server.sendmail(gmail_user, [recipient], message.as_string())

    logger.info(
        "Gmail notification sent to %s for contact: %s",
        recipient,
        data.get("email"),
    )
