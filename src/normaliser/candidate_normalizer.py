"""
candidate_normalizer.py — Applies field-level normalization to a CandidatePartial.

All normalization is deterministic: same input -> same output.
Values that cannot be normalized are set to None (never invented).
"""
import logging

from src.models import CandidatePartial
from src.normaliser.dates import normalize_date
from src.normaliser.emails import normalize_email
from src.normaliser.names import normalize_name
from src.normaliser.phones import normalize_phone
from src.normaliser.skills import normalize_skills

logger = logging.getLogger(__name__)


class CandidateNormalizer:
    def normalize(self, partial: CandidatePartial) -> CandidatePartial:
        partial.name = normalize_name(partial.name)
        partial.emails = self._dedup([normalize_email(e) for e in partial.emails])
        partial.phones = self._dedup([normalize_phone(p) for p in partial.phones])
        partial.skills = normalize_skills(partial.skills)

        for exp in partial.experience:
            exp.start = normalize_date(exp.start)
            exp.end = normalize_date(exp.end)

        return partial

    @staticmethod
    def _dedup(items: list) -> list:
        seen: set = set()
        result = []
        for item in items:
            if item and item not in seen:
                seen.add(item)
                result.append(item)
        return result
