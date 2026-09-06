"""
Central configuration. Every secret / environment-specific value comes from
an environment variable — never hardcoded. See .env.example for the full list.
"""
import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def _bool(value, default=False):
    if value is None:
        return default
    return str(value).strip().lower() in ("1", "true", "yes", "on")


class Config:
    # ---- Core ----
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
    ENV = os.environ.get("FLASK_ENV", "production")
    DEBUG = _bool(os.environ.get("FLASK_DEBUG"), default=False)

    # ---- Database ----
    # Reads SQLALCHEMY_DATABASE_URI from .env / Render environment variables.
    # Automatically converts Supabase's 'postgres://' prefix to 'postgresql://' for SQLAlchemy compatibility.
    # Falls back to local SQLite if no environment variable is provided.
    _db_url = os.environ.get("SQLALCHEMY_DATABASE_URI")

    if _db_url:
        if _db_url.startswith("postgres://"):
            _db_url = _db_url.replace("postgres://", "postgresql://", 1)
        SQLALCHEMY_DATABASE_URI = _db_url
    else:
        SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "instance", "samunnathi.db")

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    # ---- Sessions / cookies ----
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = _bool(os.environ.get("SESSION_COOKIE_SECURE"), default=False)
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)

    # ---- Uploads ----
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", os.path.join(BASE_DIR, "uploads", "resumes"))
    MAX_CONTENT_LENGTH = 6 * 1024 * 1024  # hard server cap slightly above the 5MB resume limit
    RESUME_MAX_SIZE_BYTES = 5 * 1024 * 1024
    RESUME_ALLOWED_EXTENSIONS = {"pdf", "doc", "docx"}
    RESUME_ALLOWED_MIME_TYPES = {
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }

    # ---- Mail ----
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", "587"))
    MAIL_USE_TLS = _bool(os.environ.get("MAIL_USE_TLS"), default=True)
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", os.environ.get("MAIL_USERNAME"))
    ADMIN_NOTIFY_EMAIL = os.environ.get("ADMIN_NOTIFY_EMAIL")

    # ---- Misc ----
    ITEMS_PER_PAGE = int(os.environ.get("ITEMS_PER_PAGE", "20"))
    NOTIFICATION_POLL_INTERVAL_MS = int(os.environ.get("NOTIFICATION_POLL_INTERVAL_MS", "15000"))
    SITE_NAME = "Samunnathi"