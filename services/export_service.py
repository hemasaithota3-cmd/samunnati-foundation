"""
Data export helpers: CSV / Excel for lists, PDF for a single application.
Resume files are never embedded - only filename + "Resume: Yes/No" metadata.
"""
import csv
import io
from datetime import datetime

from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

APP_TYPE_FIELDS = {
    "guidance": [
        ("reference_number", "Reference"), ("full_name", "Full Name"), ("email", "Email"),
        ("phone", "Phone"), ("education_level", "Education Level"), ("institution", "Institution"),
        ("location", "Location"), ("guidance_area", "Guidance Area"), ("preferred_contact", "Preferred Contact"),
        ("message", "Message"), ("status", "Status"), ("created_at", "Submitted"),
    ],
    "mentor": [
        ("reference_number", "Reference"), ("full_name", "Full Name"), ("email", "Email"), ("phone", "Phone"),
        ("location", "Location"), ("qualification", "Qualification"), ("profession", "Profession"),
        ("organization", "Organization"), ("years_experience", "Experience"), ("expertise", "Expertise"),
        ("mentoring_areas", "Mentoring Areas"), ("availability", "Availability"), ("linkedin", "LinkedIn"),
        ("portfolio", "Portfolio"), ("status", "Status"), ("created_at", "Submitted"),
    ],
    "volunteer": [
        ("reference_number", "Reference"), ("full_name", "Full Name"), ("email", "Email"), ("phone", "Phone"),
        ("location", "Location"), ("education_profession", "Education/Profession"), ("skills", "Skills"),
        ("areas_of_interest", "Areas of Interest"), ("availability", "Availability"), ("status", "Status"),
        ("created_at", "Submitted"),
    ],
}


def _row_value(item, field):
    value = getattr(item, field, "")
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M")
    return value if value is not None else ""


def build_csv(app_type: str, items) -> io.BytesIO:
    fields = APP_TYPE_FIELDS[app_type]
    headers = [label for _, label in fields]
    if app_type == "mentor":
        headers += ["Resume", "Resume File"]

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(headers)
    for item in items:
        row = [_row_value(item, field) for field, _ in fields]
        if app_type == "mentor":
            row += ["Yes", item.resume_original_name]
        writer.writerow(row)
    return io.BytesIO(buffer.getvalue().encode("utf-8-sig"))


def build_excel(app_type: str, items) -> io.BytesIO:
    fields = APP_TYPE_FIELDS[app_type]
    wb = Workbook()
    ws = wb.active
    ws.title = app_type.capitalize()

    headers = [label for _, label in fields]
    if app_type == "mentor":
        headers += ["Resume", "Resume File"]
    ws.append(headers)
    for cell in ws[1]:
        cell.font = cell.font.copy(bold=True)

    for item in items:
        row = [_row_value(item, field) for field, _ in fields]
        if app_type == "mentor":
            row += ["Yes", item.resume_original_name]
        ws.append(row)

    for column_cells in ws.columns:
        length = max(len(str(cell.value)) if cell.value is not None else 0 for cell in column_cells)
        ws.column_dimensions[column_cells[0].column_letter].width = min(max(length + 2, 10), 45)

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer


def build_application_pdf(app_type: str, item) -> io.BytesIO:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=22 * mm, bottomMargin=18 * mm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleNavy", parent=styles["Title"], textColor=colors.HexColor("#0E2A46"))
    label_style = ParagraphStyle("Label", parent=styles["Normal"], textColor=colors.HexColor("#55606F"), fontSize=9)
    value_style = ParagraphStyle("Value", parent=styles["Normal"], fontSize=11, spaceAfter=8)

    fields = APP_TYPE_FIELDS[app_type]
    story = [
        Paragraph(f"Samunnathi — {app_type.capitalize()} Application", title_style),
        Paragraph(item.reference_number, styles["Heading3"]),
        Spacer(1, 10),
    ]

    table_data = []
    for field, label in fields:
        value = _row_value(item, field)
        table_data.append([Paragraph(label, label_style), Paragraph(str(value), value_style)])

    if app_type == "mentor":
        table_data.append([Paragraph("Resume", label_style), Paragraph(item.resume_original_name, value_style)])

    table = Table(table_data, colWidths=[110, 360])
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E5E5")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(table)

    doc.build(story)
    buffer.seek(0)
    return buffer
