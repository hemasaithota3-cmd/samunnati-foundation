import re

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^[0-9+\-\s()]{7,20}$")


def is_valid_email(value: str) -> bool:
    return bool(value) and bool(EMAIL_RE.match(value.strip()))


def is_valid_phone(value: str) -> bool:
    return bool(value) and bool(PHONE_RE.match(value.strip()))


def require(form, field, errors, label=None, min_len=1, max_len=5000):
    value = (form.get(field) or "").strip()
    if len(value) < min_len:
        errors[field] = f"{label or field.replace('_', ' ').title()} is required."
    elif len(value) > max_len:
        errors[field] = f"{label or field.replace('_', ' ').title()} is too long."
    return value


def validate_common_contact_fields(form, errors):
    """Shared checks used by all three forms: name, email, phone, consent."""
    full_name = require(form, "full_name", errors, "Full name")
    email = (form.get("email") or "").strip()
    if not email:
        errors["email"] = "Email is required."
    elif not is_valid_email(email):
        errors["email"] = "Please enter a valid email address."

    phone = (form.get("phone") or "").strip()
    if not phone:
        errors["phone"] = "Phone number is required."
    elif not is_valid_phone(phone):
        errors["phone"] = "Please enter a valid phone number."

    if not form.get("consent"):
        errors["consent"] = "Please accept the consent checkbox to continue."

    return full_name, email, phone
