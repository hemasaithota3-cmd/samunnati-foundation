import io
from datetime import datetime

from flask import (
    Blueprint, render_template, request, redirect, url_for, flash,
    current_app, send_file, jsonify, abort
)
from flask_login import login_required, current_user

from models import db
from models.guidance import GuidanceRequest, APPLICATION_STATUSES
from models.mentor import MentorApplication
from models.volunteer import VolunteerApplication
from models.notification import Notification
from services import email_service, notification_service
from services.export_service import build_csv, build_excel, build_application_pdf
from services.file_service import fetch_resume, delete_resume


admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


MODEL_MAP = {
    "guidance": GuidanceRequest,
    "mentor": MentorApplication,
    "volunteer": VolunteerApplication,
}


SEARCHABLE_FIELDS = [
    "full_name",
    "email",
    "phone",
    "reference_number"
]


def _apply_filters(model, args):
    query = model.query

    search = (args.get("q") or "").strip()

    if search:
        like = f"%{search}%"

        from sqlalchemy import or_

        clauses = [
            getattr(model, f).ilike(like)
            for f in SEARCHABLE_FIELDS
            if hasattr(model, f)
        ]

        query = query.filter(or_(*clauses))

    status = (args.get("status") or "").strip()

    if status and status in APPLICATION_STATUSES:
        query = query.filter(model.status == status)

    date_from = (args.get("date_from") or "").strip()
    date_to = (args.get("date_to") or "").strip()

    if date_from:
        try:
            query = query.filter(
                model.created_at >= datetime.strptime(
                    date_from,
                    "%Y-%m-%d"
                )
            )
        except ValueError:
            pass

    if date_to:
        try:
            query = query.filter(
                model.created_at <= datetime.strptime(
                    date_to,
                    "%Y-%m-%d"
                )
            )
        except ValueError:
            pass

    return query.order_by(model.created_at.desc())


def _paginated_query(model, args):
    query = _apply_filters(model, args)

    page = max(
        int(args.get("page", 1) or 1),
        1
    )

    per_page = current_app.config["ITEMS_PER_PAGE"]

    return query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )


# ---------------------------------------------------------------- dashboard

@admin_bp.route("/dashboard")
@login_required
def dashboard():

    stats = {
        "guidance_total": GuidanceRequest.query.count(),

        "mentor_total": MentorApplication.query.count(),

        "volunteer_total": VolunteerApplication.query.count(),

        "unread_notifications": notification_service.unread_count(),

        "new_count": (
            GuidanceRequest.query.filter_by(status="NEW").count()
            + MentorApplication.query.filter_by(status="NEW").count()
            + VolunteerApplication.query.filter_by(status="NEW").count()
        ),

        "reviewing_count": (
            GuidanceRequest.query.filter_by(status="REVIEWING").count()
            + MentorApplication.query.filter_by(status="REVIEWING").count()
            + VolunteerApplication.query.filter_by(status="REVIEWING").count()
        ),

        "approved_count": (
            GuidanceRequest.query.filter_by(status="APPROVED").count()
            + MentorApplication.query.filter_by(status="APPROVED").count()
            + VolunteerApplication.query.filter_by(status="APPROVED").count()
        ),
    }

    recent = []

    for app_type, model in MODEL_MAP.items():

        for item in model.query.order_by(
            model.created_at.desc()
        ).limit(5).all():

            recent.append({
                "type": app_type,
                "item": item
            })

    recent.sort(
        key=lambda r: r["item"].created_at,
        reverse=True
    )

    recent = recent[:8]

    recent_notifications = Notification.query.order_by(
        Notification.created_at.desc()
    ).limit(6).all()

    return render_template(
        "admin/dashboard.html",
        stats=stats,
        recent=recent,
        recent_notifications=recent_notifications
    )


# ------------------------------------------------------------ generic list

def _render_list(app_type):

    model = MODEL_MAP[app_type]

    pagination = _paginated_query(
        model,
        request.args
    )

    return render_template(
        f"admin/{app_type}_list.html",
        pagination=pagination,
        items=pagination.items,
        statuses=APPLICATION_STATUSES,
        args=request.args,
    )


@admin_bp.route("/guidance")
@login_required
def guidance_list():
    return _render_list("guidance")


@admin_bp.route("/mentors")
@login_required
def mentor_list():
    return _render_list("mentor")


@admin_bp.route("/volunteers")
@login_required
def volunteer_list():
    return _render_list("volunteer")


# ---------------------------------------------------------------- details

def _mark_notification_read_for(app_type, item_id):

    notification = Notification.query.filter_by(
        application_type=app_type,
        reference_id=item_id,
        is_read=False
    ).first()

    if notification:
        notification.is_read = True
        db.session.commit()


@admin_bp.route("/guidance/<int:item_id>")
@login_required
def guidance_detail(item_id):

    item = GuidanceRequest.query.get_or_404(item_id)

    if not item.is_read:
        item.is_read = True
        db.session.commit()

    _mark_notification_read_for(
        "guidance",
        item_id
    )

    return render_template(
        "admin/guidance_details.html",
        item=item,
        statuses=APPLICATION_STATUSES
    )


@admin_bp.route("/mentors/<int:item_id>")
@login_required
def mentor_detail(item_id):

    item = MentorApplication.query.get_or_404(item_id)

    if not item.is_read:
        item.is_read = True
        db.session.commit()

    _mark_notification_read_for(
        "mentor",
        item_id
    )

    return render_template(
        "admin/mentor_details.html",
        item=item,
        statuses=APPLICATION_STATUSES
    )


@admin_bp.route("/volunteers/<int:item_id>")
@login_required
def volunteer_detail(item_id):

    item = VolunteerApplication.query.get_or_404(item_id)

    if not item.is_read:
        item.is_read = True
        db.session.commit()

    _mark_notification_read_for(
        "volunteer",
        item_id
    )

    return render_template(
        "admin/volunteer_details.html",
        item=item,
        statuses=APPLICATION_STATUSES
    )


# ------------------------------------------------------------ status change

@admin_bp.route(
    "/application/<app_type>/<int:item_id>/status",
    methods=["POST"]
)
@login_required
def change_status(app_type, item_id):

    model = MODEL_MAP.get(app_type)

    if not model:
        abort(404)

    item = model.query.get_or_404(item_id)

    new_status = request.form.get("status")

    if new_status not in APPLICATION_STATUSES:

        flash(
            "Invalid status.",
            "error"
        )

    else:

        item.status = new_status

        db.session.commit()

        flash(
            f"Status updated to {new_status}.",
            "success"
        )

    return redirect(
        request.referrer
        or url_for("admin.dashboard")
    )


# ---------------------------------------------------------------- resend

@admin_bp.route(
    "/application/<app_type>/<int:item_id>/resend",
    methods=["POST"]
)
@login_required
def resend_email(app_type, item_id):

    model = MODEL_MAP.get(app_type)

    if not model:
        abort(404)

    item = model.query.get_or_404(item_id)

    success = email_service.send_confirmation_email(
        app_type,
        item
    )

    flash(
        "Confirmation email resent."
        if success
        else "Email could not be sent — check mail configuration.",

        "success"
        if success
        else "error"
    )

    return redirect(
        request.referrer
        or url_for("admin.dashboard")
    )


@admin_bp.route(
    "/application/<app_type>/<int:item_id>/reply",
    methods=["POST"]
)
@login_required
def reply_email(app_type, item_id):

    model = MODEL_MAP.get(app_type)

    if not model:
        abort(404)

    item = model.query.get_or_404(item_id)

    subject = (
        request.form.get("subject")
        or ""
    ).strip()

    body = (
        request.form.get("body")
        or ""
    ).strip()

    if not subject or not body:

        flash(
            "Subject and message are required to send a reply.",
            "error"
        )

        return redirect(
            request.referrer
            or url_for("admin.dashboard")
        )

    success, error = email_service.send_admin_reply(
        app_type,
        item,
        subject,
        body
    )

    flash(
        "Reply sent."
        if success
        else f"Reply could not be sent: {error}",

        "success"
        if success
        else "error"
    )

    return redirect(
        request.referrer
        or url_for("admin.dashboard")
    )


# ------------------------------------------------------------ resume access

@admin_bp.route("/mentor/<int:item_id>/resume")
@login_required
def mentor_resume_view(item_id):

    item = MentorApplication.query.get_or_404(item_id)

    current_app.logger.info(
        "Resume request: mentor_id=%s, stored_name=%s",
        item_id,
        item.resume_stored_name
    )

    result = fetch_resume(item.resume_stored_name)

    if not result:

        current_app.logger.error(
            "Resume file NOT FOUND in storage: mentor_id=%s, stored_name=%s",
            item_id,
            item.resume_stored_name
        )

        abort(404)

    data, content_type = result

    current_app.logger.info(
        "Resume file found in storage for mentor_id=%s",
        item_id
    )

    return send_file(
        io.BytesIO(data),
        mimetype=content_type,
        as_attachment=False
    )


@admin_bp.route("/mentor/<int:item_id>/resume/download")
@login_required
def mentor_resume_download(item_id):

    item = MentorApplication.query.get_or_404(item_id)

    current_app.logger.info(
        "Resume download request: mentor_id=%s, stored_name=%s",
        item_id,
        item.resume_stored_name
    )

    result = fetch_resume(item.resume_stored_name)

    if not result:

        current_app.logger.error(
            "Resume download file NOT FOUND in storage: mentor_id=%s, stored_name=%s",
            item_id,
            item.resume_stored_name
        )

        abort(404)

    data, content_type = result

    return send_file(
        io.BytesIO(data),
        mimetype=content_type,
        as_attachment=True,
        download_name=item.resume_original_name
    )


# ---------------------------------------------------------------- deletion

@admin_bp.route(
    "/application/<app_type>/<int:item_id>/delete",
    methods=["POST"]
)
@login_required
def delete_application(app_type, item_id):

    model = MODEL_MAP.get(app_type)

    if not model:
        abort(404)

    item = model.query.get_or_404(item_id)

    if app_type == "mentor":

        try:
            delete_resume(item.resume_stored_name)

        except Exception:

            current_app.logger.warning(
                "Could not remove resume from storage for mentor #%s",
                item_id
            )

    Notification.query.filter_by(
        application_type=app_type,
        reference_id=item_id
    ).delete()

    db.session.delete(item)

    db.session.commit()

    flash(
        "Application deleted.",
        "success"
    )

    return redirect(
        url_for(f"admin.{app_type}_list")
    )


# --------------------------------------------------------------- PDF export

@admin_bp.route(
    "/application/<app_type>/<int:item_id>/pdf"
)
@login_required
def application_pdf(app_type, item_id):

    model = MODEL_MAP.get(app_type)

    if not model:
        abort(404)

    item = model.query.get_or_404(item_id)

    buffer = build_application_pdf(
        app_type,
        item
    )

    return send_file(
        buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"{item.reference_number}.pdf"
    )


# ---------------------------------------------------------- list exports

@admin_bp.route(
    "/<app_type>/export/<fmt>"
)
@login_required
def export_list(app_type, fmt):

    model = MODEL_MAP.get(app_type)

    if not model or fmt not in {"csv", "excel"}:
        abort(404)

    items = _apply_filters(
        model,
        request.args
    ).limit(5000).all()

    if fmt == "csv":

        buffer = build_csv(
            app_type,
            items
        )

        return send_file(
            buffer,
            mimetype="text/csv",
            as_attachment=True,
            download_name=f"{app_type}_export.csv"
        )

    buffer = build_excel(
        app_type,
        items
    )

    return send_file(
        buffer,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=f"{app_type}_export.xlsx"
    )


# ------------------------------------------------------------- notifications

@admin_bp.route("/notifications")
@login_required
def notifications():

    items = Notification.query.order_by(
        Notification.created_at.desc()
    ).limit(100).all()

    return render_template(
        "admin/notifications.html",
        items=items
    )


@admin_bp.route(
    "/notifications/<int:notification_id>/read",
    methods=["POST"]
)
@login_required
def mark_notification_read(notification_id):

    notification = Notification.query.get_or_404(
        notification_id
    )

    notification.is_read = True

    db.session.commit()

    return jsonify({
        "ok": True
    })


@admin_bp.route("/notifications/poll")
@login_required
def notifications_poll():

    """Lightweight polling endpoint the dashboard calls periodically."""

    unread = notification_service.unread_count()

    latest = Notification.query.order_by(
        Notification.created_at.desc()
    ).limit(5).all()

    return jsonify({
        "unread_count": unread,

        "latest": [
            {
                "id": n.id,
                "title": n.title,
                "message": n.message,
                "url": n.detail_url(),
                "is_read": n.is_read,
                "created_at": n.created_at.strftime("%H:%M"),
            }
            for n in latest
        ],
    })