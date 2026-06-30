import re


def normalize_name(name: str | None) -> str | None:
    if not name:
        return None

    # Collapse extra whitespace, then title-case
    return re.sub(r"\s+", " ", name.strip()).title()
