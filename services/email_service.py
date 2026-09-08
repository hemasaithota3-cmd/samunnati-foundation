"""
Email service for Samunnathi.

- Sends confirmation emails to applicants.
- Sends notification emails to admin.
- Logs email attempts to email_logs.
- Email failures NEVER cause application submission to fail.
"""

import logging
import smtplib

from email.mime.text import MIMEText
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
            "Your reference number is:\n\n"
            "{reference}\n\n"
            "Our team will review your request and contact you soon.\n\n"
            "Regards,\n"
            "Samunnathi Team"
        ),
    },

    "mentor": {
        "subject": (
            "Thank you for your interest in becoming "
            "a Samunnathi Mentor"
        ),
        "body": (
            "Hi {name},\n\n"
            "Thank you for your interest in becoming a mentor "
            "with Samunnathi.\n\n"
            "We have successfully received your mentor "
            "application and resume.\n\n"
            "Your reference number is:\n\n"
            "{reference}\n\n"
            "Our team will review your application and "
            "contact you soon.\n\n"
            "Regards,\n"
            "Samunnathi Team"
        ),
    },

    "volunteer": {
        "subject": "Thank you for volunteering with Samunnathi",
        "body": (
            "Hi {name},\n\n"
            "Thank you for your interest in volunteering "
            "with Samunnathi.\n\n"
            "We have successfully received your volunteer "
            "application.\n\n"
            "Your reference number is:\n\n"
            "{reference}\n\n"
            "Our team will review your application and "
            "contact you soon.\n\n"
            "Thank you for supporting the Samunnathi mission.\n\n"
            "Regards,\n"
            "Samunnathi Team"
        ),
    },
}


def _send_raw(
    to_address: str,
    subject: str,
    body: str
) -> tuple[bool, str | None]:
    """
    Send one email.

    IMPORTANT:
    This function NEVER raises an exception.
    If SMTP fails, it returns (False, error).
    """

    cfg = current_app.config

    host = cfg.get("MAIL_SERVER")
    port = cfg.get("MAIL_PORT")
    use_tls = cfg.get("MAIL_USE_TLS", True)

    username = cfg.get("MAIL_USERNAME")
    password = cfg.get("MAIL_PASSWORD")
    sender = cfg.get("MAIL_DEFAULT_SENDER")

    # ---------------------------------------------------------
    # Check configuration
    # ---------------------------------------------------------

    if not host:
        return False, "MAIL_SERVER is not configured."

    if not port:
        return False, "MAIL_PORT is not configured."

    if not username:
        return False, "MAIL_USERNAME is not configured."

    if not password:
        return False, "MAIL_PASSWORD is not configured."

    if not sender:
        return False, "MAIL_DEFAULT_SENDER is not configured."

    if not to_address:
        return False, "Recipient email address is missing."

    # ---------------------------------------------------------
    # Create email
    # ---------------------------------------------------------

    msg = MIMEText(body, "plain", "utf-8")

    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to_address

    # ---------------------------------------------------------
    # Send email
    # ---------------------------------------------------------

    try:
        logger.info(
            "Attempting to send email to %s using %s:%s",
            to_address,
            host,
            port,
        )

        # IMPORTANT:
        # Keep timeout short on Render.
        with smtplib.SMTP(
            host,
            int(port),
            timeout=10
        ) as server:

            server.ehlo()

            if use_tls:
                server.starttls()
                server.ehlo()

            server.login(username, password)

            server.sendmail(
                sender,
                [to_address],
                msg.as_string()
            )

        logger.info(
            "Email successfully sent to %s",
            to_address
        )

        return True, None

    except (smtplib.SMTPException, OSError, TimeoutError) as exc:

        error = str(exc)

        logger.error(
            "Email send failed to %s: %s",
            to_address,
            error,
        )

        # VERY IMPORTANT:
        # Never raise the exception.
        return False, error

    except Exception as exc:

        # Extra safety so email can NEVER break form submission.
        error = str(exc)

        logger.exception(
            "Unexpected email error while sending to %s",
            to_address,
        )

        return False, error


def send_confirmation_email(
    application_type: str,
    application,
    kind_override: str | None = None
) -> bool:
    """
    Sends:

    1. Confirmation email to applicant
    2. Notification email to admin

    Email failures NEVER cause the application
    database transaction to fail.

    Returns:
        True  -> applicant email sent
        False -> applicant email failed
    """

    try:
        cfg = current_app.config

        # -----------------------------------------------------
        # Check template
        # -----------------------------------------------------

        template = TEMPLATES.get(application_type)

        if not template:
            logger.error(
                "Unknown application type: %s",
                application_type
            )
            return False

        # -----------------------------------------------------
        # Applicant information
        # -----------------------------------------------------

        applicant_name = getattr(
            application,
            "full_name",
            "Applicant"
        )

        reference = getattr(
            application,
            "reference_number",
            "N/A"
        )

        applicant_email = getattr(
            application,
            "email",
            None
        )

        # -----------------------------------------------------
        # Send confirmation email
        # -----------------------------------------------------

        user_body = template["body"].format(
            name=applicant_name,
            reference=reference,
        )

        user_success, user_error = _send_raw(
            applicant_email,
            template["subject"],
            user_body,
        )

        # -----------------------------------------------------
        # Log applicant email
        # -----------------------------------------------------

        try:
            log_user = EmailLog(
                application_type=application_type,
                application_id=application.id,
                recipient=applicant_email,
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
                "Could not create user email log: %s",
                exc
            )

        # -----------------------------------------------------
        # Admin notification email
        # -----------------------------------------------------

        admin_email = cfg.get("ADMIN_NOTIFY_EMAIL")

        if admin_email:

            admin_subject = (
                f"New {application_type.title()} "
                f"Request Received [{reference}]"
            )

            admin_body = (
                "A new submission was submitted "
                "on Samunnathi App!\n\n"

                f"Type: {application_type.title()}\n"

                f"Reference: {reference}\n"

                f"Name: {getattr(application, 'full_name', 'N/A')}\n"

                f"Email: {getattr(application, 'email', 'N/A')}\n"

                f"Phone: {getattr(application, 'phone', 'N/A')}\n"

                f"Location: {getattr(application, 'location', 'N/A')}\n\n"

                "Message/Details:\n"
                f"{getattr(application, 'message', 'N/A')}\n"
            )

            admin_success, admin_error = _send_raw(
                admin_email,
                admin_subject,
                admin_body,
            )

            # -------------------------------------------------
            # Log admin email
            # -------------------------------------------------

            try:
                log_admin = EmailLog(
                    application_type=application_type,
                    application_id=application.id,
                    recipient=admin_email,
                    subject=admin_subject,
                    kind="admin_notification",
                    status=(
                        "SENT"
                        if admin_success
                        else "FAILED"
                    ),
                    error_message=(
                        None
                        if admin_success
                        else admin_error
                    ),
                )

                db.session.add(log_admin)

            except Exception as exc:
                logger.exception(
                    "Could not create admin email log: %s",
                    exc
                )

        # -----------------------------------------------------
        # Save email logs
        # -----------------------------------------------------

        try:
            db.session.commit()

        except Exception as exc:
            logger.exception(
                "Could not save email logs: %s",
                exc
            )

            # Do not allow email logging failure
            # to affect the application.
            db.session.rollback()

        # -----------------------------------------------------
        # Return applicant email status
        # -----------------------------------------------------

        return user_success

    except Exception as exc:

        # Absolute final safety net.
        #
        # Email must NEVER make the form return 500.
        logger.exception(
            "Unexpected confirmation email error: %s",
            exc
        )

        try:
            db.session.rollback()
        except Exception:
            pass

        return False


def send_admin_reply(
    application_type: str,
    application,
    subject: str,
    body: str
) -> tuple[bool, str | None]:
    """
    Send an email from admin to an applicant.

    Email failure does not raise an exception.
    """

    try:

        applicant_email = getattr(
            application,
            "email",
            None
        )

        success, error = _send_raw(
            applicant_email,
            subject,
            body
        )

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
                "Could not save admin reply email log: %s",
                exc
            )

            try:
                db.session.rollback()
            except Exception:
                pass

        return success, error

    except Exception as exc:

        logger.exception(
            "Unexpected admin reply email error: %s",
            exc
        )

        try:
            db.session.rollback()
        except Exception:
            pass

        return False, str(exc)