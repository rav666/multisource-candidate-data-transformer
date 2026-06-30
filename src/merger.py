"""
Merges one or more normalized CandidatePartials into a CanonicalCandidate, tracking provenance and assigning
confidence scores.

Merge policy (by field type):
  Scalar (name, headline, location):
      Resume wins over CSV. First non-null value from highest-priority source.

  List (emails, phones):
      Union across all sources, deduplicated.

  Skills:
      Union by canonical name; each skill's confidence reflects how many
      sources mentioned it and the quality of those sources.

  Experience / Education:
      Resume entries are preferred (richer). CSV adds only if it introduces
      a company not already represented in the resume.

  years_experience:
      Computed from normalized experience dates (not extracted directly).

  overall_confidence:
      Weighted mean of per-field confidences.
"""
from __future__ import annotations

import logging
from datetime import date
from typing import Optional

from src.models import (
    CanonicalCandidate,
    CandidatePartial,
    Education,
    Experience,
    Links,
    ProvenanceEntry,
    Skill,
)
from src.normaliser.location import normalize_location

logger = logging.getLogger(__name__)

# Higher number -> higher priority when picking a scalar winner.
SOURCE_PRIORITY: dict[str, int] = {
    "resume": 10,
    "csv": 5,
}

# Base confidence per source (0–1).
SOURCE_CONFIDENCE: dict[str, float] = {
    "resume": 0.85,
    "csv": 0.75,
}


class Merger:
    @staticmethod
    def merge(partials: list[CandidatePartial]) -> CanonicalCandidate:
        if not partials:
            raise ValueError("merge() requires at least one CandidatePartial.")

        canon = CanonicalCandidate()
        prov: list[ProvenanceEntry] = []
        field_confidences: list[float] = []

        def pick_scalar(attr: str) -> tuple[Optional[str], str]:
            """Return (best_value, winning_source) by source priority."""
            best_val, best_src = None, ""
            best_priority = -1

            for p in partials:
                value = getattr(p, attr, None)
                if not value:
                    continue

                priority = SOURCE_PRIORITY.get(p.source, 0)
                if priority > best_priority:
                    best_priority = priority
                    best_val, best_src = value, p.source

            return best_val, best_src

        def record(field: str, source: str, method: str, confidence: float) -> None:
            prov.append(ProvenanceEntry(field=field, source=source, method=method))
            field_confidences.append(confidence)

        # Full name
        val, src = pick_scalar("name")
        canon.full_name = val
        if val:
            record("full_name", src, _method(src), SOURCE_CONFIDENCE.get(src, 0.5))

        # Emails (union)
        seen_emails: set[str] = set()
        for partial in partials:
            for email in partial.emails:
                if email and email not in seen_emails:
                    seen_emails.add(email)
                    canon.emails.append(email)

        if canon.emails:
            sources_str = _sources(partials, "emails")
            record("emails", sources_str, "union", _union_conf(partials, "emails"))

        # Phones (union)
        seen_phones: set[str] = set()
        for partial in partials:
            for phones in partial.phones:
                if phones and phones not in seen_phones:
                    seen_phones.add(phones)
                    canon.phones.append(phones)

        if canon.phones:
            sources_str = _sources(partials, "phones")
            record("phones", sources_str, "union", _union_conf(partials, "phones"))

        # Location
        loc_raw, loc_src = pick_scalar("location")
        if loc_raw:
            canon.location = normalize_location(loc_raw)
            record("location", loc_src, _method(loc_src), SOURCE_CONFIDENCE.get(loc_src, 0.5))

        # Links
        merged_links: dict[str, str] = {}
        for partial in partials:
            for k, v in (partial.links or {}).items():
                if k not in merged_links and v:
                    merged_links[k] = v

        canon.links = Links(
            linkedin=merged_links.get("linkedin"),
            github=merged_links.get("github"),
            portfolio=merged_links.get("portfolio"),
            other=[v for k, v in merged_links.items() if k not in {"linkedin", "github", "portfolio"}],
        )

        # Headline
        val, src = pick_scalar("headline")
        canon.headline = val
        if val:
            record("headline", src, _method(src), SOURCE_CONFIDENCE.get(src, 0.5))

        # Skills (union w/ confidence)
        canon.skills = _merge_skills(partials)
        if canon.skills:
            avg_skill_conf = sum(s.confidence for s in canon.skills) / len(canon.skills)
            record("skills", "resume+csv", "union", avg_skill_conf)

        # Experience
        canon.experience = _merge_experience(partials)
        if canon.experience:
            exp_src = _dominant_source(partials, "experience")
            record("experience", exp_src, _method(exp_src), SOURCE_CONFIDENCE.get(exp_src, 0.5))

        # Education
        canon.education = _merge_education(partials)
        if canon.education:
            edu_src = _dominant_source(partials, "education")
            record("education", edu_src, _method(edu_src), SOURCE_CONFIDENCE.get(edu_src, 0.5))

        # Years of Experience
        canon.years_experience = _compute_years(canon.experience)

        # Finalize
        canon.provenance = prov
        canon.overall_confidence = (
            round(sum(field_confidences) / len(field_confidences), 3)
            if field_confidences else 0.0
        )

        canon.assign_id()
        return canon


def _method(source: str) -> str:
    return {"resume": "resume_parse", "csv": "csv_parse"}.get(source, "unknown")


def _sources(partials: list[CandidatePartial], attr: str) -> str:
    srcs = [p.source for p in partials if getattr(p, attr, None)]
    return "+".join(sorted(set(srcs))) or "unknown"


def _union_conf(partials: list[CandidatePartial], attr: str) -> float:
    confs = [SOURCE_CONFIDENCE.get(p.source, 0.5) for p in partials if getattr(p, attr, None)]
    if not confs:
        return 0.0

    base = max(confs)
    # Bonus if corroborated by multiple sources
    return min(1.0, base + 0.05 * (len(confs) - 1))


def _dominant_source(partials: list[CandidatePartial], attr: str) -> str:
    best_source, best_priority = "", -1
    for partial in partials:
        value = getattr(partial, attr, None)

        if value:
            priority = SOURCE_PRIORITY.get(partial.source, 0)
            if priority > best_priority:
                best_priority, best_source = priority, partial.source

    return best_source or "unknown"


def _merge_skills(partials: list[CandidatePartial]) -> list[Skill]:
    """Union of all skills; each tracks which sources mentioned it."""
    skill_map: dict[str, Skill] = {}

    for partial in partials:
        conf_base = SOURCE_CONFIDENCE.get(partial.source, 0.5)

        for skill_name in partial.skills:
            key = skill_name.lower()

            if key in skill_map:
                if partial.source not in skill_map[key].sources:
                    skill_map[key].sources.append(partial.source)
                    # Seeing skill in a second source boosts confidence
                    skill_map[key].confidence = min(1.0, skill_map[key].confidence + 0.08)

            else:
                skill_map[key] = Skill(
                    name=skill_name,
                    confidence=round(conf_base, 3),
                    sources=[partial.source],
                )

    return list(skill_map.values())


def _merge_experience(partials: list[CandidatePartial]) -> list[Experience]:
    """
    Prefer resume experience entries. CSV adds a row only if the company is not already represented in any resume entry.
    """
    resume_experiences: list[Experience] = []
    csv_experiences: list[Experience] = []

    for partial in sorted(partials, key=lambda x: SOURCE_PRIORITY.get(x.source, 0), reverse=True):
        if partial.source == "resume":
            resume_experiences.extend(partial.experience)
        else:
            csv_experiences.extend(partial.experience)

    resume_companies = {
        (experience.company or "").lower() for experience in resume_experiences if experience.company
    }

    extra: list[Experience] = [
        experience for experience in csv_experiences
        if experience.company and experience.company.lower() not in resume_companies
    ]

    return resume_experiences + extra


def _merge_education(partials: list[CandidatePartial]) -> list[Education]:
    """Prefer resume education; CSV adds rows for unknown institutions."""
    resume_edu: list[Education] = []
    csv_edu: list[Education] = []

    for partial in sorted(partials, key=lambda x: SOURCE_PRIORITY.get(x.source, 0), reverse=True):
        if partial.source == "resume":
            resume_edu.extend(partial.education)

        else:
            csv_edu.extend(partial.education)

    resume_institutions = {
        (edu.institution or "").lower() for edu in resume_edu if edu.institution
    }

    extra = [
        edu for edu in csv_edu
        if edu.institution and edu.institution.lower() not in resume_institutions
    ]

    return resume_edu + extra


def _compute_years(experience: list[Experience]) -> Optional[float]:
    """Sum experience durations from normalized YYYY-MM dates."""
    today = date.today()
    total_months = 0

    for exp in experience:
        if not exp.start:
            continue

        try:
            sy, sm = map(int, exp.start.split("-"))
            start = date(sy, sm, 1)

        except (ValueError, AttributeError):
            continue

        if exp.end:
            try:
                ey, em = map(int, exp.end.split("-"))
                end = date(ey, em, 1)

            except (ValueError, AttributeError):
                end = today

        else:
            end = today  # still in role

        months = (end.year - start.year) * 12 + (end.month - start.month)
        if months > 0:
            total_months += months

    return round(total_months / 12, 1) if total_months > 0 else None
