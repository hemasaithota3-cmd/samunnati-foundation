# ---------------------------------------------------------
# Confirmation email
# ---------------------------------------------------------
try:
    email_service.send_confirmation_email(
        "mentor",
        record
    )
except Exception as exc:
    current_app.logger.exception(
        "Confirmation email failed for mentor #%s: %s",
        record.id,
        exc
    )