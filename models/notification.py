from datetime import datetime, timezone

from models import db

NOTIFICATION_TYPES = {
    "guidance": {"label": "Guidance Request", "icon": "📩"},
    "mentor": {"label": "Mentor Application", "icon": "🎓"},
    "volunteer": {"label": "Volunteer Application", "icon": "🤝"},
}


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20), nullable=False)          # 'guidance' | 'mentor' | 'volunteer'
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    reference_id = db.Column(db.Integer, nullable=False)      # PK of the related application row
    application_type = db.Column(db.String(20), nullable=False)  # same as `type`, kept per spec's schema
    is_read = db.Column(db.Boolean, default=False, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    def detail_url(self):
        from flask import url_for
        mapping = {
            "guidance": "admin.guidance_detail",
            "mentor": "admin.mentor_detail",
            "volunteer": "admin.volunteer_detail",
        }
        endpoint = mapping.get(self.application_type)
        if not endpoint:
            return "#"
        return url_for(endpoint, item_id=self.reference_id)
