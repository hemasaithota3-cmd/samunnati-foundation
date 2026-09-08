"""
Email service for Samunnathi.

Uses Resend HTTP API instead of SMTP.

Important:
- Email failures NEVER cause application submissions to fail.
- Email failures are logged in email_logs.
- Database/application records remain saved even when email sending fails.
"""

import logging

import resend
from flask import current_app

from models import db
from models.email_log import EmailLog


logger = logging.getLogger("samunnathi.email")


# ============================================================
# EMAIL TEMPLATES
# ============================================================

TEMPLATES = {
    "guidance": {
        "subject": "Your Samunnathi Guidance Request Has Been Received",
        "body": (
            "Hi {name},\n\n"
            "Thank you for contacting Samunnathi.\n\n"
            "We have successfully received your guidance request.\n\n"
            "Your reference number is:\n\n"
            "{reference}\n\n"
            "Our team will review your request and contact you soon.\n\n"
            "Regards,\n"
            "Samunnathi Team"
        ),
    },

    "mentor": {
        "subject": "Thank you for your interest in becoming a Samunnathi Mentor",
        "body": (
            "Hi {name},\n\n"
            "Thank you for your interest in becoming a mentor with Samunnathi.\n\n"
            "We have successfully received your mentor application and resume.\n\n"
            "Your reference number is:\n\n"
            "{reference}\n\n"
            "Our team will review your application and contact you soon.\n\n"
            "Regards,\n"
            "Samunnathi Team"
        ),
    },

    "volunteer": {
        "subject": "Thank you for volunteering with Samunnathi",
        "body": (
            "Hi {name},\n\n"
            "Thank you for your interest in volunteering with Samunnathi.\n\n"
            "We have successfully received your volunteer application.\n\n"
            "Your reference number is:\n\n"
            "{reference}\n\n"
            "Our team will review your application and contact you soon.\n\n"
            "Thank you for supporting the Samunnathi mission.\n\n"
            "Regards,\n"
            "Samunnathi Team"
        ),
    },
}


# ============================================================
# SEND EMAIL USING RESEND
# ============================================================

def _send_raw(
    to_address: str,
    subject: str,
    body: str
) -> tuple[bool, str | None]:
    """
    Send one email using Resend.

    Returns:
        (True, None)  -> email sent successfully
        (False, error) -> email failed

    IMPORTANT:
    This function NEVER raises an exception.
    """

    try:
        cfg = current_app.config

        # ----------------------------------------------------
        # Get Resend API key
        # ----------------------------------------------------

        api_key = cfg.get("RESEND_API_KEY")

        if not api_key:
            error = "RESEND_API_KEY is missing."
            logger.error(error)
            return False, error

        # ----------------------------------------------------
        # Get sender
        # ----------------------------------------------------

        sender = cfg.get("MAIL_DEFAULT_SENDER")

        if not sender:
            error = "MAIL_DEFAULT_SENDER is missing."
            logger.error(error)
            return False, error

        # ----------------------------------------------------
        # Configure Resend
        # ----------------------------------------------------

        resend.api_key = api_key

        # ----------------------------------------------------
        # Send email
        # ----------------------------------------------------

        params = {
            "from": sender,
            "to": [to_address],
            "subject": subject,
            "text": body,
        }

        response = resend.Emails.send(params)

        logger.info(
            "Email sent successfully to %s",
            to_address
        )

        return True, None

    except Exception as exc:
        # ----------------------------------------------------
        # VERY IMPORTANT
        #
        # Never allow email failure to crash the application.
        # ----------------------------------------------------

        logger.exception(
            "Email send failed to %s: %s",
            to_address,
            exc
        )

        return False, str(exc)


# ============================================================
# SEND CONFIRMATION EMAIL
# ============================================================

def send_confirmation_email(
    application_type: str,
    application,
    kind_override: str | None = None
) -> bool:
    """
    Sends:

    1. Confirmation email to applicant
    2. Notification email to admin

    Email failure NEVER causes the application submission
    to fail.

    Returns:
        True  -> applicant confirmation email sent
        False -> applicant confirmation email failed
    """

    try:
        cfg = current_app.config

        # ----------------------------------------------------
        # Validate application type
        # ----------------------------------------------------

        if application_type not in TEMPLATES:
            logger.error(
                "Unknown application type: %s",
                application_type
            )
            return False

        template = TEMPLATES[application_type]

        # ====================================================
        # 1. SEND EMAIL TO APPLICANT
        # ====================================================

        applicant_name = getattr(
            application,
            "full_name",
            "Applicant"
        )

        applicant_email = getattr(
            application,
            "email",
            None
        )

        reference = getattr(
            application,
            "reference_number",
            "N/A"
        )

        if not applicant_email:
            logger.error(
                "Application has no email address."
            )

            user_success = False
            user_error = "Applicant email address is missing."

        else:
            user_body = template["body"].format(
                name=applicant_name,
                reference=reference,
            )

            user_success, user_error = _send_raw(
                applicant_email,
                template["subject"],
                user_body
            )

        # ----------------------------------------------------
        # Log applicant email
        # ----------------------------------------------------

        try:
            log_user = EmailLog(
                application_type=application_type,
                application_id=application.id,
                recipient=applicant_email or "",
                subject=template["subject"],
                kind=kind_override or "confirmation",
                status="SENT" if user_success else "FAILED",
                error_message=(
                    None
                    if user_success
                    else user_error
                ),
            )

            db.session.add(log_user)

        except Exception as exc:
            logger.exception(
                "Failed to create applicant email log: %s",
                exc
            )

        # ====================================================
        # 2. SEND EMAIL TO ADMIN
        # ====================================================

        admin_email = cfg.get("ADMIN_NOTIFY_EMAIL")

        if admin_email:

            admin_subject = (
                f"New {application_type.title()} "
                f"Request Received "
                f"[{reference}]"
            )

            admin_body = (
                "A new submission was submitted "
                "on Samunnathi App!\n\n"

                f"Type: {application_type.title()}\n"

                f"Reference: {reference}\n"

                f"Name: "
                f"{getattr(application, 'full_name', 'N/A')}\n"

                f"Email: "
                f"{getattr(application, 'email', 'N/A')}\n"

                f"Phone: "
                f"{getattr(application, 'phone', 'N/A')}\n"

                f"Location: "
                f"{getattr(application, 'location', 'N/A')}\n\n"

                "Message/Details:\n"

                f"{getattr(application, 'message', 'N/A')}\n"
            )

            admin_success, admin_error = _send_raw(
                admin_email,
                admin_subject,
                admin_body
            )

            # ------------------------------------------------
            # Log admin email
            # ------------------------------------------------

            try:
                log_admin = EmailLog(
                    application_type=application_type,
                    application_id=application.id,
                    recipient=admin_email,
                    subject=admin_subject,
                    kind="admin_notification",
                    status="SENT" if admin_success else "FAILED",
                    error_message=(
                        None
                        if admin_success
                        else admin_error
                    ),
                )

                db.session.add(log_admin)

            except Exception as exc:
                logger.exception(
                    "Failed to create admin email log: %s",
                    exc
                )

        # ----------------------------------------------------
        # Save email logs
        # ----------------------------------------------------

        try:
            db.session.commit()

        except Exception as exc:
            logger.exception(
                "Failed to commit email logs: %s",
                exc
            )

            # Don't let logging failure break the application.
            try:
                db.session.rollback()
            except Exception:
                pass

        # ----------------------------------------------------
        # Return applicant email status
        # ----------------------------------------------------

        return user_success

    except Exception as exc:
        # ====================================================
        # FINAL SAFETY NET
        # ====================================================

        logger.exception(
            "Unexpected error in send_confirmation_email: %s",
            exc
        )

        return False


# ============================================================
# ADMIN REPLY
# ============================================================

def send_admin_reply(
    application_type: str,
    application,
    subject: str,
    body: str
) -> tuple[bool, str | None]:
    """
    Send a reply from the admin to an applicant.

    Email failure does not raise an exception.
    """

    try:

        applicant_email = getattr(
            application,
            "email",
            None
        )

        if not applicant_email:
            return False, "Applicant email address is missing."

        # ----------------------------------------------------
        # Send email
        # ----------------------------------------------------

        success, error = _send_raw(
            applicant_email,
            subject,
            body
        )

        # ----------------------------------------------------
        # Log email
        # ----------------------------------------------------

        try:
            log = EmailLog(
                application_type=application_type,
                application_id=application.id,
                recipient=applicant_email,
                subject=subject,
                kind="admin_reply",
                status="SENT" if success else "FAILED",
                error_message=(
                    None
                    if success
                    else error
                ),
            )

            db.session.add(log)
            db.session.commit()

        except Exception as exc:
            logger.exception(
                "Failed to save admin reply email log: %s",
                exc
            )

            try:
                db.session.rollback()
            except Exception:
                pass

        return success, error

    except Exception as exc:

        logger.exception(
            "Unexpected error in send_admin_reply: %s",
            exc
        )

        return False, str(exc)