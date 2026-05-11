"""
Database base module for tracking archiving status and results.

Databases receive notifications about the archiving process and can
check for previously archived content. They serve as both a cache
and a reporting mechanism.
"""

from __future__ import annotations
from abc import abstractmethod
from typing import Union

from .base_module import BaseModule
from .metadata import Metadata


class Database(BaseModule):
    """
    Base class for database modules.

    Databases track archiving status and results. They receive lifecycle
    notifications (started, failed, done) and can check if a URL has
    already been archived (fetch).
    """

    def started(self, item: Metadata) -> None:
        """
        Called when archiving begins for an item.

        Args:
            item: Metadata for the item being archived
        """
        pass

    def failed(self, item: Metadata, reason: str) -> None:
        """
        Called when archiving fails.

        Args:
            item: Metadata for the failed item
            reason: Description of why archiving failed
        """
        pass

    def aborted(self, item: Metadata) -> None:
        """
        Called when archiving is cancelled by user.

        Args:
            item: Metadata for the aborted item
        """
        pass

    def fetch(self, item: Metadata) -> Union[Metadata, bool]:
        """
        Checks if item has already been archived.

        Override to implement caching logic. Returns previously archived
        Metadata if found, False otherwise.

        Args:
            item: Metadata to check

        Returns:
            Previously archived Metadata, or False if not found
        """
        return False

    @abstractmethod
    def done(self, item: Metadata, cached: bool = False) -> None:
        """
        Called when archiving completes successfully.

        Implementations should save or record the archiving results.

        Args:
            item: Completed Metadata with archived content
            cached: True if result was retrieved from cache
        """
        pass
