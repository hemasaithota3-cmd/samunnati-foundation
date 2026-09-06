from datetime import datetime, timezone

from models import db
from models.reference import format_reference

GUIDANCE_AREAS = ["Education", "Career", "Higher Studies", "Skills", "Mentorship", "Job Opportunities", "Other"]
CONTACT_METHODS = ["Email", "Phone", "WhatsApp"]
APPLICATION_STATUSES = ["NEW", "REVIEWING", "CONTACTED", "APPROVED", "REJECTED", "COMPLETED"]


class GuidanceRequest(db.Model):
    __tablename__ = "guidance_requests"

    id = db.Column(db.Integer, primary_key=True)
    reference_number = db.Column(db.String(20), unique=True, index=True)

    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(190), nullable=False, index=True)
    phone = db.Column(db.String(30), nullable=False)
    education_level = db.Column(db.String(120), nullable=False)
    institution = db.Column(db.String(200), nullable=True)
    location = db.Column(db.String(150), nullable=False)
    guidance_area = db.Column(db.String(60), nullable=False)
    preferred_contact = db.Column(db.String(30), nullable=True)
    message = db.Column(db.Text, nullable=False)

    status = db.Column(db.String(20), default="NEW", nullable=False, index=True)
    is_read = db.Column(db.Boolean, default=False, nullable=False, index=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def assign_reference(self):
        self.reference_number = format_reference("GUID", self.id)
