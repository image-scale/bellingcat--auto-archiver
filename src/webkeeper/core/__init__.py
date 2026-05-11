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
from .module import ModuleFactory, LazyBaseModule, MANIFEST_FILE, DEFAULT_MANIFEST
from .config import (
    read_yaml,
    store_yaml,
    to_dot_notation,
    from_dot_notation,
    merge_dicts,
    is_valid_config,
    EMPTY_CONFIG,
    DEFAULT_CONFIG_FILE,
)

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
    "ModuleFactory",
    "LazyBaseModule",
    "MANIFEST_FILE",
    "DEFAULT_MANIFEST",
    "read_yaml",
    "store_yaml",
    "to_dot_notation",
    "from_dot_notation",
    "merge_dicts",
    "is_valid_config",
    "EMPTY_CONFIG",
    "DEFAULT_CONFIG_FILE",
]
