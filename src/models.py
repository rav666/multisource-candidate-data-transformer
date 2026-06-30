"""
models.py — All Pydantic data models for the pipeline.

Three tiers:
  LLMResponse      → raw structured output from the LLM (resume source)
  CandidatePartial → normalised data from one source (resume OR csv)
  CanonicalCandidate → final merged record, matches the canonical spec
"""
from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ─── Sub-models (shared across tiers) ─────────────────────────────────────────

class Experience(BaseModel):
    company: Optional[str] = None
    title: Optional[str] = None
    start: Optional[str] = None   # YYYY-MM after normalisation
    end: Optional[str] = None     # YYYY-MM or null (= current)
    summary: Optional[str] = None


class Education(BaseModel):
    institution: Optional[str] = None
    degree: Optional[str] = None
    field: Optional[str] = None
    end_year: Optional[str] = None


# ─── Canonical output sub-models ──────────────────────────────────────────────

class Location(BaseModel):
    city: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None   # ISO-3166 alpha-2


class Links(BaseModel):
    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None
    other: List[str] = Field(default_factory=list)


class Skill(BaseModel):
    name: str
    confidence: float = 0.5
    sources: List[str] = Field(default_factory=list)


class ProvenanceEntry(BaseModel):
    field: str
    source: str
    method: str


# ─── Tier 1: LLM structured-output schema ─────────────────────────────────────

class LLMResponse(BaseModel):
    """Exactly what Gemini returns for a resume — no source metadata."""
    name: Optional[str] = None
    emails: List[str] = Field(default_factory=list)
    phones: List[str] = Field(default_factory=list)
    location: Optional[str] = None
    headline: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    experience: List[Experience] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)


# ─── Tier 2: Source-level partial (post-parse, pre-merge) ─────────────────────

class CandidatePartial(BaseModel):
    """One source's worth of data.  Normalised values, source-tagged."""
    source: str   # "resume" | "csv"
    method: str   # "resume_parse" | "csv_parse"

    name: Optional[str] = None
    emails: List[str] = Field(default_factory=list)
    phones: List[str] = Field(default_factory=list)
    location: Optional[str] = None          # raw string; structured in canonical
    links: Dict[str, str] = Field(default_factory=dict)
    headline: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    experience: List[Experience] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)


# ─── Tier 3: Canonical candidate (final output) ───────────────────────────────

class CanonicalCandidate(BaseModel):
    """Final merged, normalised candidate record — spec-compliant."""
    candidate_id: str = ""
    full_name: Optional[str] = None
    emails: List[str] = Field(default_factory=list)
    phones: List[str] = Field(default_factory=list)
    location: Location = Field(default_factory=Location)
    links: Links = Field(default_factory=Links)
    headline: Optional[str] = None
    years_experience: Optional[float] = None
    skills: List[Skill] = Field(default_factory=list)
    experience: List[Experience] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    provenance: List[ProvenanceEntry] = Field(default_factory=list)
    overall_confidence: float = 0.0

    def assign_id(self) -> None:
        """Deterministic ID from best-known email + normalised name."""
        key = f"{(self.full_name or '').lower()}|{sorted(self.emails)[0] if self.emails else ''}"
        self.candidate_id = hashlib.sha256(key.encode()).hexdigest()[:16]
