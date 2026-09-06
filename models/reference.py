"""
Sequential, human-readable reference numbers (e.g. GUID-000031, MENTOR-000024,
VOL-000124). Generated from each table's own auto-increment id so numbers are
gap-free per type and never collide.
"""


def format_reference(prefix: str, numeric_id: int) -> str:
    return f"{prefix}-{numeric_id:06d}"
