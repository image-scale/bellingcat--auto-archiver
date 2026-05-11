"""Console database module for logging archival status to console."""

from loguru import logger

from webkeeper.core import Database, Metadata


class ConsoleDb(Database):
    """Database that outputs archival status to the console."""

    def started(self, item: Metadata) -> None:
        """Log when archiving starts."""
        logger.info(f"STARTED {item}")

    def failed(self, item: Metadata, reason: str) -> None:
        """Log when archiving fails."""
        logger.error(f"FAILED {item}: {reason}")

    def aborted(self, item: Metadata) -> None:
        """Log when archiving is aborted."""
        logger.warning(f"ABORTED {item}")

    def done(self, item: Metadata, cached: bool = False) -> None:
        """Log when archiving completes."""
        logger.success(f"DONE {item}")
