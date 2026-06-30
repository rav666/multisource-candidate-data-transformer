"""
Parse arbitrary date strings into YYYY-MM format.

Also understands "Present" / "Current" / "Now" -> returns None (open-ended).
"""
import logging
import re

from dateutil import parser as dateutil_parser

logger = logging.getLogger(__name__)

_OPEN_ENDED = {"present", "current", "now", "ongoing", "till date", "to date"}


def normalize_date(date_str: str | None) -> str | None:
    """Return YYYY-MM string, None for open-ended/missing, or None on error."""
    if not date_str:
        return None

    cleaned = date_str.strip()
    if cleaned.lower() in _OPEN_ENDED:
        return None  # signals "still in this role"

    # Already in YYYY-MM
    if re.fullmatch(r"\d{4}-\d{2}", cleaned):
        return cleaned

    # Just a 4-digit year
    if re.fullmatch(r"\d{4}", cleaned):
        return f"{cleaned}-01"

    try:
        d = dateutil_parser.parse(cleaned, default=dateutil_parser.parse("2000-01-01"))
        return d.strftime("%Y-%m")
    except Exception:
        logger.debug("Could not parse date: %r", date_str)
        return None
