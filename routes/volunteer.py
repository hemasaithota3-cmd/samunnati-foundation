from flask import Blueprint, render_template, request, redirect, url_for, flash

from models import db
from models.volunteer import VolunteerApplication
from services import email_service, notification_service
from services.dedupe import is_recent_duplicate, mark_submitted
from services.validators import validate_common_contact_fields, require

volunteer_bp = Blueprint("volunteer", __name__)


@volunteer_bp.route("/volunteer")
def volunteer_page():
    return render_template("volunteer.html")


@volunteer_bp.route("/volunteer/submit", methods=["POST"])
def volunteer_submit():
    form = request.form
    errors = {}

    full_name, email, phone = validate_common_contact_fields(form, errors)
    location = require(form, "location", errors, "Location")
    education_profession = (form.get("education_profession") or "").strip() or None
    skills = require(form, "skills", errors, "Skills")
    areas_of_interest = require(form, "areas_of_interest", errors, "Areas of interest")
    availability = require(form, "availability", errors, "Availability")
    previous_experience = (form.get("previous_experience") or "").strip() or None
    reason = require(form, "reason", errors, "Reason", min_len=10, max_len=4000)
    message = (form.get("message") or "").strip() or None

    if errors:
        return render_template("volunteer.html", errors=errors, form_data=form, scroll_to_form=True), 400

    if is_recent_duplicate("volunteer", request.remote_addr or "", email):
        flash("It looks like you already submitted this. Our team has received it — no need to resend.", "info")
        return redirect(url_for("volunteer.volunteer_page"))

    try:
        record = VolunteerApplication(
            full_name=full_name, email=email, phone=phone, location=location,
            education_profession=education_profession, skills=skills,
            areas_of_interest=areas_of_interest, availability=availability,
            previous_experience=previous_experience, reason=reason, message=message,
        )
        db.session.add(record)
        db.session.commit()
        record.assign_reference()
        db.session.commit()
        mark_submitted("volunteer", request.remote_addr or "", email)
    except Exception:
        db.session.rollback()
        flash("Something went wrong while submitting your application. Please try again.", "error")
        return render_template("volunteer.html", form_data=form), 500

    notification_service.create_notification("volunteer", record)
    email_service.send_confirmation_email("volunteer", record)

    return redirect(url_for("volunteer.volunteer_success", reference=record.reference_number))


@volunteer_bp.route("/volunteer/success/<reference>")
def volunteer_success(reference):
    record = VolunteerApplication.query.filter_by(reference_number=reference).first_or_404()
    return render_template("success.html", record=record, kind="Volunteer Application")
