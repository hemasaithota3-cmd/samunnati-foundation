"""
Secure resume upload handling.

- Never trusts the client-supplied filename or the browser's reported
  MIME type for anything except a UX hint.
- Validates real file content via magic-byte signatures, not just the
  extension.
- Generates a random, unguessable stored filename - the original filename
  is kept only as metadata in the database.
- Files are written outside any publicly-served directory.
"""
import os
import re
import uuid
from dataclasses import dataclass

from werkzeug.utils import secure_filename

# Magic-byte signatures for the three allowed resume formats.
PDF_SIGNATURE = b"%PDF-"
ZIP_SIGNATURE = b"PK\x03\x04"       # .docx is a zip container
OLE_SIGNATURE = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"  # legacy .doc (OLE compound file)

DANGEROUS_EXTENSIONS = {
    "exe", "js", "py", "php", "sh", "bat", "cmd", "html", "htm", "svg",
    "jar", "com", "vbs", "ps1", "msi", "dll", "app", "apk",
}


@dataclass
class UploadResult:
    ok: bool
    error: str | None = None
    stored_name: str | None = None
    absolute_path: str | None = None
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


def validate_and_store_resume(file_storage, upload_folder: str, max_bytes: int, prefix: str = "mentor") -> UploadResult:
    if file_storage is None or file_storage.filename == "":
        return UploadResult(ok=False, error="Please upload your resume.")

    original_name = secure_filename(file_storage.filename) or "resume"
    extension = _extension(original_name)

    if not extension or extension in DANGEROUS_EXTENSIONS or extension not in {"pdf", "doc", "docx"}:
        return UploadResult(ok=False, error="Please upload a PDF, DOC, or DOCX resume.")

    # Size check (stream-based, avoids loading the whole file into memory twice)
    file_storage.stream.seek(0, os.SEEK_END)
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
        # check above is the authoritative guard - but we log the mismatch
        # via the caller if needed.
        pass

    os.makedirs(upload_folder, exist_ok=True)
    stored_name = f"{prefix}_{uuid.uuid4().hex[:12]}_resume.{extension}"
    # Defense in depth against path traversal even though uuid can't produce it.
    stored_name = re.sub(r"[^A-Za-z0-9_.-]", "", stored_name)
    absolute_path = os.path.join(upload_folder, stored_name)

    file_storage.save(absolute_path)

    return UploadResult(
        ok=True,
        stored_name=stored_name,
        absolute_path=absolute_path,
        relative_path=stored_name,
    )


def resume_absolute_path(upload_folder: str, stored_name: str) -> str | None:
    """
    Safely resolve a stored resume filename back to an absolute path,
    refusing anything that isn't a plain filename inside upload_folder.
    """
    if not stored_name or "/" in stored_name or "\\" in stored_name or ".." in stored_name:
        return None
    candidate = os.path.join(upload_folder, stored_name)
    upload_folder_real = os.path.realpath(upload_folder)
    candidate_real = os.path.realpath(candidate)
    if not candidate_real.startswith(upload_folder_real + os.sep):
        return None
    if not os.path.isfile(candidate_real):
        return None
    return candidate_real
