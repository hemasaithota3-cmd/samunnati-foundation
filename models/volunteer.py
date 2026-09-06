from datetime import datetime, timezone

from models import db
from models.reference import format_reference


class VolunteerApplication(db.Model):
    __tablename__ = "volunteer_applications"

    id = db.Column(db.Integer, primary_key=True)
    reference_number = db.Column(db.String(20), unique=True, index=True)

    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(190), nullable=False, index=True)
    phone = db.Column(db.String(30), nullable=False)
    location = db.Column(db.String(150), nullable=False)

    education_profession = db.Column(db.String(200), nullable=True)
    skills = db.Column(db.Text, nullable=False)
    areas_of_interest = db.Column(db.Text, nullable=False)
    availability = db.Column(db.String(60), nullable=False)
    previous_experience = db.Column(db.Text, nullable=True)
    reason = db.Column(db.Text, nullable=False)
    message = db.Column(db.Text, nullable=True)

    status = db.Column(db.String(20), default="NEW", nullable=False, index=True)
    is_read = db.Column(db.Boolean, default=False, nullable=False, index=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def assign_reference(self):
        self.reference_number = format_reference("VOL", self.id)
