from abc import ABC, abstractmethod


class BaseParser(ABC):
    @abstractmethod
    def parse(self, source: str):
        """Parse a source and return extracted candidate data."""
