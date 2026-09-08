from flask import Blueprint, render_template, request, redirect, url_for, flash

from models import db
from models.volunteer import VolunteerApplication
from services import email_service, notification_service
from services.dedupe import is_recent_duplicate, mark_submitted
from services.validators import validate_common_contact_fields, require


# =========================================================
# Blueprint
# =========================================================

volunteer_bp = Blueprint("volunteer", __name__)


# =========================================================
# Volunteer Page
# =========================================================

@volunteer_bp.route("/volunteer")
def volunteer_page():
    return render_template("volunteer.html")


# =========================================================
# Volunteer Form Submit
# =========================================================

@volunteer_bp.route("/volunteer/submit", methods=["POST"])
def volunteer_submit():

    form = request.form
    errors = {}

    # -----------------------------------------------------
    # Validate common fields
    # -----------------------------------------------------

    full_name, email, phone = validate_common_contact_fields(
        form,
        errors
    )

    location = require(
        form,
        "location",
        errors,
        "Location"
    )

    education_profession = (
        form.get("education_profession") or ""
    ).strip() or None

    skills = require(
        form,
        "skills",
        errors,
        "Skills"
    )

    areas_of_interest = require(
        form,
        "areas_of_interest",
        errors,
        "Areas of interest"
    )

    availability = require(
        form,
        "availability",
        errors,
        "Availability"
    )

    previous_experience = (
        form.get("previous_experience") or ""
    ).strip() or None

    reason = require(
        form,
        "reason",
        errors,
        "Reason",
        min_len=10,
        max_len=4000
    )

    message = (
        form.get("message") or ""
    ).strip() or None


    # -----------------------------------------------------
    # Stop if validation failed
    # -----------------------------------------------------

    if errors:
        return render_template(
            "volunteer.html",
            errors=errors,
            form_data=form,
            scroll_to_form=True
        ), 400


    # -----------------------------------------------------
    # Duplicate submission check
    # -----------------------------------------------------

    if is_recent_duplicate(
        "volunteer",
        request.remote_addr or "",
        email
    ):
        flash(
            "It looks like you already submitted this. "
            "Our team has received it — no need to resend.",
            "info"
        )

        return redirect(
            url_for("volunteer.volunteer_page")
        )


    # -----------------------------------------------------
    # Save application
    # -----------------------------------------------------

    try:

        record = VolunteerApplication(
            full_name=full_name,
            email=email,
            phone=phone,
            location=location,
            education_profession=education_profession,
            skills=skills,
            areas_of_interest=areas_of_interest,
            availability=availability,
            previous_experience=previous_experience,
            reason=reason,
            message=message,
        )

        db.session.add(record)

        db.session.commit()


        # -------------------------------------------------
        # Generate reference number
        # -------------------------------------------------

        record.assign_reference()

        db.session.commit()


        # -------------------------------------------------
        # Mark submission
        # -------------------------------------------------

        mark_submitted(
            "volunteer",
            request.remote_addr or "",
            email
        )


    except Exception as exc:

        db.session.rollback()

        # Log the actual database error
        # so it appears in Render logs.
        try:
            from flask import current_app

            current_app.logger.exception(
                "Failed to save volunteer application: %s",
                exc
            )
        except Exception:
            pass

        flash(
            "Something went wrong while submitting your "
            "application. Please try again.",
            "error"
        )

        return render_template(
            "volunteer.html",
            form_data=form,
            errors=errors
        ), 500


    # =====================================================
    # Database save succeeded
    # =====================================================

    # -----------------------------------------------------
    # Create notification
    # -----------------------------------------------------

    try:

        notification_service.create_notification(
            "volunteer",
            record
        )

    except Exception as exc:

        # Notification failure must NOT make the
        # successfully saved application fail.

        try:
            from flask import current_app

            current_app.logger.exception(
                "Volunteer notification failed for #%s: %s",
                record.id,
                exc
            )
        except Exception:
            pass


    # -----------------------------------------------------
    # Send confirmation email
    # -----------------------------------------------------

    try:

        email_service.send_confirmation_email(
            "volunteer",
            record
        )

    except Exception as exc:

        # Email failure must NOT cause the form
        # submission to return HTTP 500.

        try:
            from flask import current_app

            current_app.logger.exception(
                "Confirmation email failed for volunteer #%s: %s",
                record.id,
                exc
            )
        except Exception:
            pass


    # -----------------------------------------------------
    # Success page
    # -----------------------------------------------------

    return redirect(
        url_for(
            "volunteer.volunteer_success",
            reference=record.reference_number
        )
    )


# =========================================================
# Volunteer Success Page
# =========================================================

@volunteer_bp.route("/volunteer/success/<reference>")
def volunteer_success(reference):

    record = VolunteerApplication.query.filter_by(
        reference_number=reference
    ).first_or_404()

    return render_template(
        "success.html",
        record=record,
        kind="Volunteer Application"
    )