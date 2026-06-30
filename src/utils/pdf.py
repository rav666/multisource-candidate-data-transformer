import logging

import pdfplumber

logger = logging.getLogger(__name__)


def extract_text(pdf_path: str) -> str:
    """Extract all text from a PDF, page by page."""
    text = ""

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

    logger.debug("Extracted %d characters from %s", len(text), pdf_path)
    return text
