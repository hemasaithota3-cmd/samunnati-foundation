"""
Lightweight duplicate-submission guard. Not a replacement for a real rate
limiter (Flask-Limiter + Redis) in a multi-process deployment, but enough to
stop a double-click or an accidental double-submit from creating two rows.

Keyed by (form_type, ip, email) with a short cooldown window. Only a
SUCCESSFUL submission starts the cooldown - a failed validation attempt
(bad file, missing field, etc.) must never block the person's next real
attempt.
"""
import time
import threading

_lock = threading.Lock()
_recent_submissions: dict[tuple[str, str, str], float] = {}
COOLDOWN_SECONDS = 20


def _key(form_type: str, ip: str, email: str):
    return (form_type, ip, (email or "").lower())


def _cleanup(now: float) -> None:
    stale = [k for k, ts in _recent_submissions.items() if now - ts > COOLDOWN_SECONDS]
    for k in stale:
        _recent_submissions.pop(k, None)


def is_recent_duplicate(form_type: str, ip: str, email: str) -> bool:
    """Read-only check - does NOT record anything. Call before inserting."""
    key = _key(form_type, ip, email)
    now = time.time()
    with _lock:
        _cleanup(now)
        last = _recent_submissions.get(key)
        return last is not None and (now - last) < COOLDOWN_SECONDS


def mark_submitted(form_type: str, ip: str, email: str) -> None:
    """Call ONLY after a submission has been successfully saved to the DB."""
    key = _key(form_type, ip, email)
    with _lock:
        _recent_submissions[key] = time.time()
