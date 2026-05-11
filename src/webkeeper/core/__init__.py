"""Core data structures and base classes for the archiving framework."""

from .media import Media
from .metadata import Metadata
from .base_module import BaseModule, MODULE_TYPES, ArchiveError, SetupError
from .feeder import Feeder
from .extractor import Extractor
from .enricher import Enricher
from .database import Database
from .storage import Storage
from .formatter import Formatter

__all__ = [
    "Media",
    "Metadata",
    "BaseModule",
    "MODULE_TYPES",
    "ArchiveError",
    "SetupError",
    "Feeder",
    "Extractor",
    "Enricher",
    "Database",
    "Storage",
    "Formatter",
]
