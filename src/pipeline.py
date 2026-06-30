"""
pipeline.py — End-to-end pipeline: parse -> normalise -> merge -> project -> validate.

Usage:
    result = Pipeline().run(resume_path="...", csv_path="...", config_path="...")
"""
import logging

from src.merger import Merger
from src.models import CanonicalCandidate, CandidatePartial
from src.normaliser.candidate_normalizer import CandidateNormalizer
from src.parsers.csv_parser import CSVParser
from src.parsers.resume_parser import ResumeParser
from src.projector import Projector

logger = logging.getLogger(__name__)


class Pipeline:

    def __init__(self) -> None:
        self._normalizer = CandidateNormalizer()
        self._projector = Projector()

    def run(
            self, resume_path: str | None = None, csv_path: str | None = None, config_path: str | None = None,
            csv_row_index: int = 0
    ) -> dict:
        """
        Run the full pipeline.

        Args:
            resume_path:   Path to PDF resume.
            csv_path:      Path to recruiter CSV file.
            config_path:   Path to JSON projection config (optional).
            csv_row_index: Which CSV row to use when multiple are present (default 0 = first candidate).

        Returns:
            dict — the final (optionally reshaped) canonical profile.
        """
        partials: list[CandidatePartial] = []

        # 1. Parse
        if resume_path:
            logger.info("Parsing resume:", resume_path)
            partial = ResumeParser().parse(resume_path)
            partials.append(partial)

        if csv_path:
            logger.info("Parsing CSV: ", csv_path)
            csv_partials = CSVParser().parse(csv_path)

            if csv_partials:
                if csv_row_index < len(csv_partials):
                    partials.append(csv_partials[csv_row_index])

                else:
                    logger.warning(
                        "csv_row_index %d out of range (%d rows); using first row.", csv_row_index,
                        len(csv_partials)
                    )
                    partials.append(csv_partials[0])

        if not partials:
            raise ValueError("At least one source (resume or CSV) must be provided.")

        # 2. Normalize each partial
        logger.info("Normalising %d source(s).", len(partials))
        partials = [self._normalizer.normalize(p) for p in partials]

        # 3. Merge
        logger.info("Merging sources.")
        canonical: CanonicalCandidate = Merger.merge(partials)

        # 4. Validate
        self._validate(canonical)

        # 5. Project (optional config)
        config = None
        if config_path:
            logger.info("Applying projection config: %s", config_path)
            config = Projector.load_config(config_path)

        return self._projector.project(canonical, config)

    @staticmethod
    def _validate(canonical: CanonicalCandidate):
        """Log warnings for missing critical fields; never raise."""
        if not canonical.full_name:
            logger.warning("Validation: full_name is null.")

        if not canonical.emails:
            logger.warning("Validation: no emails found.")

        if not canonical.phones:
            logger.warning("Validation: no phones found.")

        if not canonical.experience:
            logger.warning("Validation: no experience entries found.")
