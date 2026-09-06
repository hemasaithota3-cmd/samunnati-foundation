from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app

from models import db
from models.mentor import MentorApplication, AVAILABILITY_OPTIONS
from services import email_service, notification_service
from services.dedupe import is_recent_duplicate, mark_submitted
from services.file_service import validate_and_store_resume
from services.validators import validate_common_contact_fields, require
from datetime import datetime, timezone
import os

mentor_bp = Blueprint("mentor", __name__)


@mentor_bp.route("/mentor")
def mentor_page():
    return render_template("mentor.html", availability_options=AVAILABILITY_OPTIONS)


@mentor_bp.route("/mentor/submit", methods=["POST"])
def mentor_submit():
    form = request.form
    errors = {}

    full_name, email, phone = validate_common_contact_fields(form, errors)
    location = require(form, "location", errors, "Location")
    qualification = require(form, "qualification", errors, "Qualification")
    profession = require(form, "profession", errors, "Profession")
    organization = (form.get("organization") or "").strip()
    years_experience = (form.get("years_experience") or "").strip()
    expertise = require(form, "expertise", errors, "Areas of expertise")
    mentoring_areas = require(form, "mentoring_areas", errors, "Areas you can mentor")
    availability = form.get("availability", "").strip()
    if availability not in AVAILABILITY_OPTIONS:
        errors["availability"] = "Please select your availability."
    linkedin = (form.get("linkedin") or "").strip() or None
    portfolio = (form.get("portfolio") or "").strip() or None
    reason = require(form, "reason", errors, "Reason", min_len=10, max_len=4000)
    message = (form.get("message") or "").strip() or None

    if not errors and is_recent_duplicate("mentor", request.remote_addr or "", email):
        flash("It looks like you already submitted this. Our team has received it — no need to resend.", "info")
        return redirect(url_for("mentor.mentor_page"))

    upload_result = validate_and_store_resume(
        request.files.get("resume"),
        upload_folder=current_app.config["UPLOAD_FOLDER"],
        max_bytes=current_app.config["RESUME_MAX_SIZE_BYTES"],
        prefix="mentor",
    )
    if not upload_result.ok:
        errors["resume"] = upload_result.error

    if errors:
        return render_template(
            "mentor.html", availability_options=AVAILABILITY_OPTIONS,
            errors=errors, form_data=form, scroll_to_form=True,
        ), 400

    try:
        record = MentorApplication(
            full_name=full_name, email=email, phone=phone, location=location,
            qualification=qualification, profession=profession, organization=organization or None,
            years_experience=years_experience or None, expertise=expertise, mentoring_areas=mentoring_areas,
            availability=availability, linkedin=linkedin, portfolio=portfolio,
            reason=reason, message=message,
            resume_original_name=request.files["resume"].filename,
            resume_stored_name=upload_result.stored_name,
            resume_path=upload_result.relative_path,
            resume_uploaded_at=datetime.now(timezone.utc),
        )
        db.session.add(record)
        db.session.commit()
        record.assign_reference()
        db.session.commit()
        mark_submitted("mentor", request.remote_addr or "", email)
    except Exception:
        db.session.rollback()
        # Clean up the orphaned file since the DB row was never created.
        try:
            if upload_result.absolute_path and os.path.exists(upload_result.absolute_path):
                os.remove(upload_result.absolute_path)
        except OSError:
            pass
        flash("Something went wrong while submitting your application. Please try again.", "error")
        return render_template("mentor.html", availability_options=AVAILABILITY_OPTIONS, form_data=form), 500

    notification_service.create_notification("mentor", record)
    email_service.send_confirmation_email("mentor", record)

    return redirect(url_for("mentor.mentor_success", reference=record.reference_number))


@mentor_bp.route("/mentor/success/<reference>")
def mentor_success(reference):
    record = MentorApplication.query.filter_by(reference_number=reference).first_or_404()
    return render_template("success.html", record=record, kind="Mentor Application", resume_uploaded=True)
