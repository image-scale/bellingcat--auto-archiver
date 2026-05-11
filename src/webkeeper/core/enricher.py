"""
Enricher base module for adding metadata to archived content.

Enrichers process archived content after extraction to add additional
metadata such as hashes, screenshots, thumbnails, or external references.
They operate on Metadata objects in-place.
"""

from __future__ import annotations
from abc import abstractmethod

from .base_module import BaseModule
from .metadata import Metadata


class Enricher(BaseModule):
    """
    Base class for enricher modules.

    Enrichers add additional information to archived content. They receive
    Metadata objects after extraction and modify them in place to add
    computed values, external lookups, or transformations.
    """

    @abstractmethod
    def enrich(self, to_enrich: Metadata) -> None:
        """
        Enriches a Metadata object with additional information.

        Implementations should modify the Metadata object in place,
        adding computed properties, external references, or transformations
        to the media files.

        Args:
            to_enrich: Metadata object to enrich
        """
        pass
