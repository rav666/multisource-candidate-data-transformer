import re

_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def normalize_email(email: str) -> str | None:
    """Strip whitespace, lowercase, validate basic format."""
    if not email:
        return None

    cleaned = email.strip().lower()
    return cleaned if _EMAIL_RE.match(cleaned) else None
