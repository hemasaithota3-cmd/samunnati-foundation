"""
Email sending, isolated behind one function so routes never touch smtplib
directly. A failed send is logged to email_logs and returns False — it never
raises, and it never causes an application record to be rolled back.
"""
import logging

import resend
from flask import current_app

from models import db
from models.email_log import EmailLog

logger = logging.getLogger("samunnathi.email")

TEMPLATES = {
    "guidance": {
        "subject": "Your Samunnathi Guidance Request Has Been Received",
        "body": (
            "Hi {name},\n\n"
            "Thank you for contacting Samunnathi.\n\n"
            "We have successfully received your guidance request.\n\n"
            "Your reference number is:\n\n{reference}\n\n"
            "Our team will review your request and contact you soon.\n\n"
            "Regards,\nSamunnathi Team"
        ),
    },
    "mentor": {
        "subject": "Thank you for your interest in becoming a Samunnathi Mentor",
        "body": (
            "Hi {name},\n\n"
            "Thank you for your interest in becoming a mentor with Samunnathi.\n\n"
            "We have successfully received your mentor application and resume.\n\n"
            "Your reference number is:\n\n{reference}\n\n"
            "Our team will review your application and contact you soon.\n\n"
            "Regards,\nSamunnathi Team"
        ),
    },
    "volunteer": {
        "subject": "Thank you for volunteering with Samunnathi",
        "body": (
            "Hi {name},\n\n"
            "Thank you for your interest in volunteering with Samunnathi.\n\n"
            "We have successfully received your volunteer application.\n\n"
            "Your reference number is:\n\n{reference}\n\n"
            "Our team will review your application and contact you soon.\n\n"
            "Thank you for supporting the Samunnathi mission.\n\n"
            "Regards,\nSamunnathi Team"
        ),
    },
}


def _send_raw(to_address: str, subject: str, body: str) -> tuple[bool, str | None]:
    cfg = current_app.config
    api_key = cfg.get("RESEND_API_KEY")
    if not api_key:
        return False, "Email is not configured (RESEND_API_KEY missing)."

    sender = cfg.get("MAIL_DEFAULT_SENDER") or "Samunnathi <onboarding@resend.dev>"

    try:
        resend.api_key = api_key
        params = {
            "from": sender,
            "to": [to_address],
            "subject": subject,
            "text": body,
        }
        resend.Emails.send(params)
        return True, None
    except Exception as exc:  # noqa: BLE001 - catch and log any Resend API failure
        logger.error("Email send failed to %s: %s", to_address, exc)
        return False, str(exc)


def send_confirmation_email(application_type: str, application, kind_override: str | None = None) -> bool:
    """
    Sends auto-confirmation email to the user AND notification email to the admin.
    Logs attempts to email_logs. Never raises an exception.
    """
    cfg = current_app.config
    template = TEMPLATES[application_type]

    # 1. Send Confirmation Email to User
    user_body = template["body"].format(
        name=getattr(application, "full_name", "Applicant"),
        reference=getattr(application, "reference_number", "N/A"),
    )
    user_success, user_error = _send_raw(application.email, template["subject"], user_body)

    # Log User Email status
    log_user = EmailLog(
        application_type=application_type,
        application_id=application.id,
        recipient=application.email,
        subject=template["subject"],
        kind=kind_override or "confirmation",
        status="SENT" if user_success else "FAILED",
        error_message=None if user_success else user_error,
    )
    db.session.add(log_user)

    # 2. Send Notification Email to Admin
    admin_email = cfg.get("ADMIN_NOTIFY_EMAIL")
    if admin_email:
        admin_subject = f"New {application_type.title()} Request Received [{getattr(application, 'reference_number', 'N/A')}]"
        admin_body = (
            f"A new submission was submitted on Samunnathi App!\n\n"
            f"Type: {application_type.title()}\n"
            f"Reference: {getattr(application, 'reference_number', 'N/A')}\n"
            f"Name: {getattr(application, 'full_name', 'N/A')}\n"
            f"Email: {getattr(application, 'email', 'N/A')}\n"
            f"Phone: {getattr(application, 'phone', 'N/A')}\n"
            f"Location: {getattr(application, 'location', 'N/A')}\n\n"
            f"Message/Details:\n{getattr(application, 'message', 'N/A')}\n"
        )
        admin_success, admin_error = _send_raw(admin_email, admin_subject, admin_body)

        # Log Admin Email status
        log_admin = EmailLog(
            application_type=application_type,
            application_id=application.id,
            recipient=admin_email,
            subject=admin_subject,
            kind="admin_notification",
            status="SENT" if admin_success else "FAILED",
            error_message=None if admin_success else admin_error,
        )
        db.session.add(log_admin)

    db.session.commit()
    return user_success


def send_admin_reply(application_type: str, application, subject: str, body: str) -> tuple[bool, str | None]:
    success, error = _send_raw(application.email, subject, body)
    log = EmailLog(
        application_type=application_type,
        application_id=application.id,
        recipient=application.email,
        subject=subject,
        kind="admin_reply",
        status="SENT" if success else "FAILED",
        error_message=None if success else error,
    )
    db.session.add(log)
    db.session.commit()
    return success, error