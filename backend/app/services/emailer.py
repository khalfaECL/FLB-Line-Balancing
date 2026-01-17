import smtplib
from email.message import EmailMessage
from pathlib import Path

from app.core.config import get_settings


def is_email_enabled() -> bool:
    settings = get_settings()
    return bool(settings.smtp_enabled and settings.smtp_host and settings.smtp_from)


def _smtp_client(settings):
    if settings.smtp_use_ssl:
        return smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port)

    server = smtplib.SMTP(settings.smtp_host, settings.smtp_port)
    if settings.smtp_use_tls:
        server.starttls()
    return server


def _send_message(message: EmailMessage) -> None:
    settings = get_settings()
    server = _smtp_client(settings)
    try:
        if settings.smtp_user and settings.smtp_password:
            server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(message)
    finally:
        server.quit()


def _build_frontend_link(token: str, kind: str) -> str:
    settings = get_settings()
    base = settings.frontend_base_url.rstrip("/")
    return f"{base}/?{kind}={token}"


def send_report_email(to_email: str, report_path: str, job_id: str) -> None:
    settings = get_settings()
    if not is_email_enabled():
        return

    message = EmailMessage()
    message["Subject"] = f"Line Balancing Report {job_id}"
    message["From"] = settings.smtp_from
    message["To"] = to_email
    message.set_content(
        "Your line balancing report is ready. "
        "Please find the PDF attached to this email."
    )

    path = Path(report_path)
    with path.open("rb") as handle:
        message.add_attachment(
            handle.read(),
            maintype="application",
            subtype="pdf",
            filename=path.name,
        )

    _send_message(message)


def send_verification_email(to_email: str, token: str) -> None:
    settings = get_settings()
    if not is_email_enabled():
        return

    link = _build_frontend_link(token, "verify")
    message = EmailMessage()
    message["Subject"] = "Verify your Line Balancing account"
    message["From"] = settings.smtp_from
    message["To"] = to_email
    message.set_content(
        "Please verify your email to activate your client space. "
        f"Open this link: {link}"
    )

    _send_message(message)


def send_password_reset_email(to_email: str, token: str) -> None:
    settings = get_settings()
    if not is_email_enabled():
        return

    link = _build_frontend_link(token, "reset")
    message = EmailMessage()
    message["Subject"] = "Reset your Line Balancing password"
    message["From"] = settings.smtp_from
    message["To"] = to_email
    message.set_content(
        "A password reset was requested for your account. "
        f"Open this link to set a new password: {link}"
    )

    _send_message(message)