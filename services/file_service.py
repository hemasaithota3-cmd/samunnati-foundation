"""
Secure resume upload handling.

- Never trusts the client-supplied filename or the browser's reported
  MIME type for anything except a UX hint.
- Validates real file content via magic-byte signatures, not just the
  extension.
- Generates a random, unguessable stored object key - the original
  filename is kept only as metadata in the database.
- The actual file bytes are persisted to Supabase Storage (see
  storage_service.py), NOT to Render's local disk, since Render's
  filesystem is ephemeral and wiped on every deploy/restart.
"""
import logging
import re
import uuid
from dataclasses import dataclass

from werkzeug.utils import secure_filename

from services import storage_service

logger = logging.getLogger("samunnathi.resume")

# Magic-byte signatures for the three allowed resume formats.
PDF_SIGNATURE = b"%PDF-"
ZIP_SIGNATURE = b"PK\x03\x04"       # .docx is a zip container
OLE_SIGNATURE = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"  # legacy .doc (OLE compound file)

DANGEROUS_EXTENSIONS = {
    "exe", "js", "py", "php", "sh", "bat", "cmd", "html", "htm", "svg",
    "jar", "com", "vbs", "ps1", "msi", "dll", "app", "apk",
}

CONTENT_TYPES = {
    "pdf": "application/pdf",
    "doc": "application/msword",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


@dataclass
class UploadResult:
    ok: bool
    error: str | None = None
    # Supabase Storage object key. This is the same value written to both
    # the `resume_stored_name` and `resume_path` columns (see note in
    # models/mentor.py / migration notes) - the columns already existed for
    # the old local-filename scheme and are simply reused to hold the new
    # storage key, so no schema change is required.
    stored_name: str | None = None
    relative_path: str | None = None


def _extension(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def _sniff_and_validate_signature(head: bytes, extension: str) -> bool:
    if extension == "pdf":
        return head.startswith(PDF_SIGNATURE)
    if extension == "docx":
        return head.startswith(ZIP_SIGNATURE)
    if extension == "doc":
        return head.startswith(OLE_SIGNATURE)
    return False


def validate_and_store_resume(file_storage, max_bytes: int, prefix: str = "mentor") -> UploadResult:
    if file_storage is None or file_storage.filename == "":
        return UploadResult(ok=False, error="Please upload your resume.")

    original_name = secure_filename(file_storage.filename) or "resume"
    extension = _extension(original_name)

    if not extension or extension in DANGEROUS_EXTENSIONS or extension not in {"pdf", "doc", "docx"}:
        return UploadResult(ok=False, error="Please upload a PDF, DOC, or DOCX resume.")

    # Size check (stream-based, avoids loading the whole file into memory twice)
    file_storage.stream.seek(0, 2)  # SEEK_END
    size = file_storage.stream.tell()
    file_storage.stream.seek(0)
    if size == 0:
        return UploadResult(ok=False, error="The uploaded file is empty.")
    if size > max_bytes:
        return UploadResult(ok=False, error="Resume size must not exceed 5 MB.")

    # Content signature check - guards against a renamed .exe etc.
    head = file_storage.stream.read(8)
    file_storage.stream.seek(0)
    if not _sniff_and_validate_signature(head, extension):
        return UploadResult(ok=False, error="This file doesn't look like a valid PDF, DOC, or DOCX. Please re-export and try again.")

    # Reported MIME type as a secondary signal only (never trusted alone).
    reported_mime = (file_storage.mimetype or "").lower()
    allowed_mimes = {
        "pdf": {"application/pdf"},
        "doc": {"application/msword", "application/octet-stream"},
        "docx": {
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/octet-stream",
            "application/zip",
        },
    }
    if reported_mime and reported_mime not in allowed_mimes[extension]:
        # Not fatal on its own (browsers are inconsistent), the signature
        # check above is the authoritative guard.
        pass

    stored_name = f"{prefix}_{uuid.uuid4().hex[:12]}_resume.{extension}"
    # Defense in depth against path traversal even though uuid can't produce it.
    stored_name = re.sub(r"[^A-Za-z0-9_.-]", "", stored_name)

    data = file_storage.stream.read()
    file_storage.stream.seek(0)

    try:
        storage_service.upload_bytes(stored_name, data, CONTENT_TYPES[extension])
    except storage_service.StorageError as exc:
        logger.error("Resume upload to Supabase Storage failed: %s", exc)
        return UploadResult(ok=False, error="We couldn't upload your resume right now. Please try again in a moment.")

    return UploadResult(
        ok=True,
        stored_name=stored_name,
        relative_path=stored_name,
    )


def fetch_resume(stored_name: str) -> tuple[bytes, str] | None:
    """
    Download a previously-uploaded resume's bytes + content type from
    Supabase Storage, for the admin view/download routes.

    Returns None if the file can't be retrieved (missing config, deleted
    object, network error, etc.) so the caller can 404 cleanly.
    """
    if not stored_name:
        return None

    extension = _extension(stored_name)
    content_type = CONTENT_TYPES.get(extension, "application/octet-stream")

    try:
        data = storage_service.download_bytes(stored_name)
    except storage_service.StorageError as exc:
        logger.error("Resume download from Supabase Storage failed for %s: %s", stored_name, exc)
        return None

    return data, content_type


def delete_resume(stored_name: str) -> bool:
    """
    Delete a resume from Supabase Storage.

    Used when: (a) the application DB save fails after the resume was
    already uploaded, and (b) an admin deletes an application. Never
    raises - a failed cleanup must not break the calling route.
    """
    if not stored_name:
        return True
    return storage_service.delete_object(stored_name)
