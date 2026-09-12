"""
Supabase Storage client for persistent resume storage.

Render's local filesystem is ephemeral (wiped on every deploy/restart), so
resumes can no longer be saved to disk in production. This module talks to
Supabase Storage over HTTPS using the project's service role key, so the
same Postgres/Supabase project that already holds the application data also
holds the resume files.

Only the backend (using the service role key) can read/write/delete
objects - the bucket is expected to be PRIVATE. Nothing here exposes
resumes publicly; admin routes stream the bytes through Flask after the
normal @login_required check.

Configuration (environment variables):
    SUPABASE_URL               e.g. https://xxxxx.supabase.co
    SUPABASE_SERVICE_ROLE_KEY  Supabase service_role key (NOT the anon key)
    SUPABASE_RESUME_BUCKET     Storage bucket name (default: "resumes")
"""
import logging
import os

import requests

logger = logging.getLogger("samunnathi.storage")

REQUEST_TIMEOUT_SECONDS = 20


class StorageError(Exception):
    """Raised whenever Supabase Storage can't be reached or refuses a request."""


def _config():
    url = (os.environ.get("SUPABASE_URL") or "").rstrip("/")
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    bucket = os.environ.get("SUPABASE_RESUME_BUCKET", "resumes")

    if not url:
        raise StorageError("SUPABASE_URL is not configured.")
    if not service_key:
        raise StorageError("SUPABASE_SERVICE_ROLE_KEY is not configured.")

    return url, service_key, bucket


def _headers(service_key: str, content_type: str | None = None) -> dict:
    headers = {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
    }
    if content_type:
        headers["Content-Type"] = content_type
    return headers


def _object_url(base_url: str, bucket: str, object_key: str) -> str:
    return f"{base_url}/storage/v1/object/{bucket}/{object_key}"


def upload_bytes(object_key: str, data: bytes, content_type: str) -> None:
    """Upload (or overwrite) an object in the resume bucket. Raises StorageError on failure."""
    base_url, service_key, bucket = _config()
    url = _object_url(base_url, bucket, object_key)

    try:
        response = requests.post(
            url,
            headers={**_headers(service_key, content_type), "x-upsert": "true"},
            data=data,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        raise StorageError(f"Could not reach Supabase Storage: {exc}") from exc

    if response.status_code not in (200, 201):
        raise StorageError(
            f"Supabase Storage upload failed ({response.status_code}): {response.text[:300]}"
        )


def download_bytes(object_key: str) -> bytes:
    """Download an object's raw bytes from the resume bucket. Raises StorageError on failure."""
    base_url, service_key, bucket = _config()
    url = _object_url(base_url, bucket, object_key)

    try:
        response = requests.get(url, headers=_headers(service_key), timeout=REQUEST_TIMEOUT_SECONDS)
    except requests.RequestException as exc:
        raise StorageError(f"Could not reach Supabase Storage: {exc}") from exc

    if response.status_code != 200:
        raise StorageError(
            f"Supabase Storage download failed ({response.status_code}): {response.text[:300]}"
        )

    return response.content


def delete_object(object_key: str) -> bool:
    """
    Delete an object from the resume bucket.

    Never raises - deletion failures (e.g. already gone, network hiccup) are
    logged and swallowed, since a failed cleanup must never break an admin
    action or a form-submission rollback.
    """
    try:
        base_url, service_key, bucket = _config()
    except StorageError as exc:
        logger.error("Cannot delete %s - storage not configured: %s", object_key, exc)
        return False

    url = _object_url(base_url, bucket, object_key)

    try:
        response = requests.delete(url, headers=_headers(service_key), timeout=REQUEST_TIMEOUT_SECONDS)
    except requests.RequestException as exc:
        logger.error("Could not reach Supabase Storage while deleting %s: %s", object_key, exc)
        return False

    if response.status_code not in (200, 204):
        logger.error(
            "Supabase Storage delete failed for %s (%s): %s",
            object_key,
            response.status_code,
            response.text[:300],
        )
        return False

    return True
