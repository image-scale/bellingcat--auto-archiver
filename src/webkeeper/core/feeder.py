"""
Feeder base module for providing URLs to archive.

Feeders are the entry point of the archiving pipeline. They iterate over
URLs from various sources (CLI, CSV files, Google Sheets, etc.) and yield
Metadata objects for each URL to be processed.
"""

from __future__ import annotations
from abc import abstractmethod

from .base_module import BaseModule
from .metadata import Metadata


class Feeder(BaseModule):
    """
    Base class for feeder modules.

    Feeders provide URLs to the archiving pipeline by implementing __iter__
    to yield Metadata objects. Each Metadata object represents a single
    URL to be archived.
    """

    @abstractmethod
    def __iter__(self) -> Metadata:
        """
        Yields Metadata objects for URLs to archive.

        Implementations should yield Metadata objects, typically created via
        Metadata().set_url(url). The iteration ends when all URLs have been
        yielded.

        Yields:
            Metadata objects representing URLs to archive
        """
        return None
