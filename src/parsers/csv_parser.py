"""
Parses recruiter CSV exports into CandidatePartial records.

Expected columns (any subset is fine; missing columns yield null):
  name, email, phone, title, current_company, location
"""
import csv
import logging
import re
from typing import List

from src.models import CandidatePartial, Experience
from src.parsers.parser_base import BaseParser

logger = logging.getLogger(__name__)


class CSVParser(BaseParser):
    """One CandidatePartial per CSV row."""

    def parse(self, path: str) -> List[CandidatePartial]:  # type: ignore[override]
        results: List[CandidatePartial] = []

        try:
            with open(path, newline="", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)

                for i, row in enumerate(reader):
                    partial = self._row_to_partial(row)
                    results.append(partial)

        except FileNotFoundError:
            logger.error("CSV not found: %s", path)

        except Exception as exc:
            logger.error("CSV parse error (%s): %s", path, exc)

        return results

    @staticmethod
    def _row_to_partial(row: dict) -> CandidatePartial:
        def get(key: str) -> str | None:
            value = (row.get(key) or "").strip()
            return value if value else None

        partial = CandidatePartial(source="csv", method="csv_parse")
        partial.name = get("name")

        email = get("email")
        if email:
            partial.emails.append(email)

        phone = get("phone")
        if phone:
            partial.phones.append(phone)

        partial.headline = get("title")
        partial.location = get("location")

        company = get("current_company")
        title = get("title")
        if company or title:
            partial.experience.append(
                Experience(company=company, title=title)
            )

        # Skills: split on comma / semicolon / pipe, trim whitespace, drop empties.
        # Raw strings only — canonicalization happens later in CandidateNormalizer,
        # the same step resume skills go through.
        skills_raw = get("skills")
        if skills_raw:
            parts = re.split(r"[,;|]", skills_raw)
            partial.skills = [s.strip() for s in parts if s.strip()]

        # Capture any link columns if present
        for link_key in ("linkedin", "github", "portfolio"):
            val = get(link_key)
            if val:
                partial.links[link_key] = val

        return partial
