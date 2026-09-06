from flask import Blueprint, render_template, request, redirect, url_for, flash

from models import db
from models.guidance import GuidanceRequest, GUIDANCE_AREAS, CONTACT_METHODS
from services import email_service, notification_service
from services.dedupe import is_recent_duplicate, mark_submitted
from services.validators import validate_common_contact_fields, require

guidance_bp = Blueprint("guidance", __name__)


@guidance_bp.route("/guidance")
def guidance_page():
    return render_template("guidance.html", guidance_areas=GUIDANCE_AREAS, contact_methods=CONTACT_METHODS)


@guidance_bp.route("/guidance/submit", methods=["POST"])
def guidance_submit():
    form = request.form
    errors = {}

    full_name, email, phone = validate_common_contact_fields(form, errors)
    education_level = require(form, "education_level", errors, "Education level")
    location = require(form, "location", errors, "Location")
    guidance_area = form.get("guidance_area", "").strip()
    if guidance_area not in GUIDANCE_AREAS:
        errors["guidance_area"] = "Please select an area of guidance."
    message = require(form, "message", errors, "Message", min_len=10, max_len=4000)
    institution = (form.get("institution") or "").strip()
    preferred_contact = form.get("preferred_contact", "").strip() or None

    if errors:
        return render_template(
            "guidance.html",
            guidance_areas=GUIDANCE_AREAS,
            contact_methods=CONTACT_METHODS,
            errors=errors,
            form_data=form,
            scroll_to_form=True,
        ), 400

    if is_recent_duplicate("guidance", request.remote_addr or "", email):
        flash("It looks like you already submitted this. Our team has received it — no need to resend.", "info")
        return redirect(url_for("guidance.guidance_page"))

    try:
        record = GuidanceRequest(
            full_name=full_name, email=email, phone=phone,
            education_level=education_level, institution=institution or None,
            location=location, guidance_area=guidance_area,
            preferred_contact=preferred_contact, message=message,
        )
        db.session.add(record)
        db.session.commit()
        record.assign_reference()
        db.session.commit()
        mark_submitted("guidance", request.remote_addr or "", email)
    except Exception:
        db.session.rollback()
        flash("Something went wrong while submitting your request. Please try again.", "error")
        return render_template(
            "guidance.html", guidance_areas=GUIDANCE_AREAS, contact_methods=CONTACT_METHODS,
            form_data=form,
        ), 500

    notification_service.create_notification("guidance", record)
    email_service.send_confirmation_email("guidance", record)

    return redirect(url_for("guidance.guidance_success", reference=record.reference_number))


@guidance_bp.route("/guidance/success/<reference>")
def guidance_success(reference):
    record = GuidanceRequest.query.filter_by(reference_number=reference).first_or_404()
    return render_template("success.html", record=record, kind="Guidance Request")
