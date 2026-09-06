from datetime import datetime, timezone

from models import db


class EmailLog(db.Model):
    __tablename__ = "email_logs"

    id = db.Column(db.Integer, primary_key=True)
    application_type = db.Column(db.String(20), nullable=False)  # guidance | mentor | volunteer
    application_id = db.Column(db.Integer, nullable=False, index=True)
    recipient = db.Column(db.String(190), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    kind = db.Column(db.String(30), default="confirmation")  # confirmation | admin_reply
    status = db.Column(db.String(20), default="SENT")  # SENT | FAILED
    error_message = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
