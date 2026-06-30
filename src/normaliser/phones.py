import logging

import phonenumbers

logger = logging.getLogger(__name__)


def normalize_phone(phone: str, default_region: str = "IN") -> str | None:
    """Return E.164 string or None if unparseable."""
    if not phone:
        return None

    try:
        parsed = phonenumbers.parse(phone, default_region)
        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)

    except Exception:
        pass

    logger.debug("Could not parse phone: %r", phone)
    return None
