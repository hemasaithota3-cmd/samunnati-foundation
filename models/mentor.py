from datetime import datetime, timezone

from models import db
from models.reference import format_reference

AVAILABILITY_OPTIONS = ["Weekdays", "Weekends", "Evenings", "Flexible"]


class MentorApplication(db.Model):
    __tablename__ = "mentor_applications"

    id = db.Column(db.Integer, primary_key=True)
    reference_number = db.Column(db.String(20), unique=True, index=True)

    # Personal information
    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(190), nullable=False, index=True)
    phone = db.Column(db.String(30), nullable=False)
    location = db.Column(db.String(150), nullable=False)

    # Professional information
    qualification = db.Column(db.String(150), nullable=False)
    profession = db.Column(db.String(150), nullable=False)
    organization = db.Column(db.String(200), nullable=True)
    years_experience = db.Column(db.String(30), nullable=True)
    expertise = db.Column(db.Text, nullable=False)
    mentoring_areas = db.Column(db.Text, nullable=False)
    availability = db.Column(db.String(60), nullable=False)

    # Online profile
    linkedin = db.Column(db.String(255), nullable=True)
    portfolio = db.Column(db.String(255), nullable=True)

    # Application
    reason = db.Column(db.Text, nullable=False)
    message = db.Column(db.Text, nullable=True)

    # Resume (never publicly exposed; stored filename is random/unguessable)
    resume_original_name = db.Column(db.String(255), nullable=False)
    resume_stored_name = db.Column(db.String(255), nullable=False, unique=True)
    resume_path = db.Column(db.String(500), nullable=False)
    resume_uploaded_at = db.Column(db.DateTime, nullable=True)

    status = db.Column(db.String(20), default="NEW", nullable=False, index=True)
    is_read = db.Column(db.Boolean, default=False, nullable=False, index=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def assign_reference(self):
        self.reference_number = format_reference("MENTOR", self.id)
