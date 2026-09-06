import logging

from models import db
from models.notification import Notification, NOTIFICATION_TYPES

logger = logging.getLogger("samunnathi.notifications")


def create_notification(app_type: str, application) -> Notification | None:
    """
    Creates a notification for a newly-submitted application. Called only
    AFTER the application row has been committed successfully. If this fails,
    it is logged but does not roll back or delete the already-saved
    application - the admin can still find it in the relevant list.
    """
    try:
        meta = NOTIFICATION_TYPES[app_type]
        noun = "request" if app_type == "guidance" else "application"
        extra = " 📄 Resume uploaded" if app_type == "mentor" else ""
        notification = Notification(
            type=app_type,
            title=f"New {meta['label']}",
            message=f"{application.full_name} submitted a new {app_type} {noun}.{extra}",
            reference_id=application.id,
            application_type=app_type,
        )
        db.session.add(notification)
        db.session.commit()
        return notification
    except Exception:  # noqa: BLE001
        db.session.rollback()
        logger.exception("Failed to create notification for %s #%s", app_type, application.id)
        return None


def unread_count() -> int:
    return Notification.query.filter_by(is_read=False).count()
