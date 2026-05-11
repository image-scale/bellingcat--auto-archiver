"""
Formatter base module for creating output files from archived content.

Formatters convert Metadata into presentable formats like HTML reports
or JSON files. They produce a final Media object that summarizes the
archived content.
"""

from __future__ import annotations
from abc import abstractmethod

from .base_module import BaseModule
from .media import Media
from .metadata import Metadata


class Formatter(BaseModule):
    """
    Base class for formatter modules.

    Formatters create output files from archived Metadata. They produce
    a single Media object (e.g., HTML file) that can be stored and
    serves as the primary output of the archiving process.
    """

    @abstractmethod
    def format(self, item: Metadata) -> Media:
        """
        Formats archived content into an output file.

        Implementations should create a file (HTML, JSON, etc.) summarizing
        the archived content and return it as a Media object.

        Args:
            item: Metadata to format

        Returns:
            Media object for the formatted output, or None
        """
        return None
