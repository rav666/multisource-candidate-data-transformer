"""
resume_parser.py — Parses a PDF resume via pdfplumber -> Gemini LLM.

Returns a single CandidatePartial tagged source="resume".
"""
import logging

from src.llm.llm_extractor import call_llm
from src.models import CandidatePartial
from src.parsers.parser_base import BaseParser
from src.utils.pdf import extract_text

logger = logging.getLogger(__name__)


class ResumeParser(BaseParser):

    def parse(self, pdf_path: str) -> CandidatePartial:  # type: ignore[override]
        # 1. Extract raw text from PDF
        text = ""

        try:
            text = extract_text(pdf_path)

        except Exception as exc:
            logger.error("PDF extraction failed (%s): %s — continuing with empty text.", pdf_path, exc)

        if not text.strip():
            logger.warning("Empty PDF text for %s — LLM will return nulls.", pdf_path)

        # 2. Call LLM to structure the text
        llm = call_llm(text)

        # 3. Convert LLMResponse -> CandidatePartial
        return CandidatePartial(
            source="resume",
            method="resume_parse",
            name=llm.name,
            emails=llm.emails,
            phones=llm.phones,
            location=llm.location,
            headline=llm.headline,
            skills=llm.skills,
            experience=llm.experience,
            education=llm.education,
        )
