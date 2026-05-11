"""
Orchestrator that coordinates the full archiving pipeline.

The orchestrator is the central coordinator of the archiving process. It:
1. Loads and configures all modules based on config
2. Iterates URLs from feeders
3. Runs extractors to download content
4. Runs enrichers to add metadata
5. Stores media to configured storages
6. Formats output
7. Notifies databases of status
"""

from __future__ import annotations
from tempfile import TemporaryDirectory
import traceback
from typing import Generator, List, Type
from urllib.parse import urlparse, parse_qsl, urlencode

from .metadata import Metadata
from .media import Media
from .module import ModuleFactory
from .base_module import BaseModule, SetupError, MODULE_TYPES
from .feeder import Feeder
from .extractor import Extractor
from .enricher import Enricher
from .database import Database
from .storage import Storage
from .formatter import Formatter


TRACKING_PARAMS = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "fbclid", "gclid"}


def clean_url(url: str) -> str:
    """Removes tracking parameters from URL."""
    parsed = urlparse(url)
    clean_qs = [(k, v) for k, v in parse_qsl(parsed.query) if k not in TRACKING_PARAMS]
    return parsed._replace(query=urlencode(clean_qs)).geturl()


def check_url_or_raise(url: str) -> bool:
    """Validates URL is safe to process."""
    if not (url.startswith("http://") or url.startswith("https://")):
        raise ValueError(f"Invalid URL scheme for url {url}")

    parsed = urlparse(url)
    if not parsed.hostname:
        raise ValueError(f"Invalid URL hostname for url {url}")

    if parsed.hostname == "localhost":
        raise ValueError(f"Localhost URLs cannot be parsed for security reasons (for url {url})")

    return True


class Orchestrator:
    """
    Central coordinator for the archiving pipeline.

    Manages the full lifecycle of archiving URLs: loading modules,
    iterating feeders, extracting content, enriching, storing, and
    notifying databases.
    """

    feeders: List[Type[Feeder]]
    extractors: List[Type[Extractor]]
    enrichers: List[Type[Enricher]]
    databases: List[Type[Database]]
    storages: List[Type[Storage]]
    formatters: List[Type[Formatter]]

    def __init__(self):
        self.module_factory = ModuleFactory()
        self.config = {}
        self.setup_finished = False

        self.feeders = []
        self.extractors = []
        self.enrichers = []
        self.databases = []
        self.storages = []
        self.formatters = []

    def setup(self, config: dict) -> None:
        """
        Configures the orchestrator with modules from config.

        Loads all modules specified in config['steps'] for each module type.

        Args:
            config: Full configuration dict with 'steps' section
        """
        if self.setup_finished:
            return

        self.config = config
        steps = config.get("steps", {})

        module_paths = config.get("module_paths", [])
        self.module_factory.setup_paths(module_paths)

        for module_type in MODULE_TYPES:
            step_modules = []
            module_names = steps.get(f"{module_type}s", [])

            for module_name in module_names:
                try:
                    module = self.module_factory.get_module(module_name, config)
                    step_modules.append(module)
                except Exception as e:
                    raise SetupError(f"Failed to load {module_type} '{module_name}': {e}")

            setattr(self, f"{module_type}s", step_modules)

        self.setup_finished = True

    def feed(self) -> Generator[Metadata, None, None]:
        """
        Processes all URLs from configured feeders.

        Yields:
            Metadata for each archived URL
        """
        for feeder in self.feeders:
            for item in feeder:
                result = self.feed_item(item)
                if result:
                    yield result

        self.cleanup()

    def feed_item(self, item: Metadata) -> Metadata:
        """
        Processes a single item through the archiving pipeline.

        Creates a temporary directory for the session and handles
        errors gracefully.

        Args:
            item: Metadata with URL to archive

        Returns:
            Archived Metadata, or None on error
        """
        tmp_dir = None
        try:
            tmp_dir = TemporaryDirectory(dir="./")

            for module in self.all_modules:
                module.tmp_dir = tmp_dir.name

            return self.archive(item)

        except KeyboardInterrupt:
            for db in self.databases:
                db.aborted(item)
            self.cleanup()
            raise

        except Exception as e:
            for db in self.databases:
                if isinstance(e, AssertionError):
                    db.failed(item, str(e))
                else:
                    db.failed(item, "unexpected error")
            return None

        finally:
            if tmp_dir:
                for module in self.all_modules:
                    module.tmp_dir = None
                tmp_dir.cleanup()

    def archive(self, result: Metadata) -> Metadata:
        """
        Runs the archiving pipeline for a single URL.

        1. Sanitizes URL
        2. Notifies databases of start
        3. Tries extractors until one succeeds
        4. Runs all enrichers
        5. Stores all media
        6. Formats result
        7. Notifies databases of completion

        Args:
            result: Metadata with URL to archive

        Returns:
            Archived Metadata with status
        """
        original_url = result.get_url().strip()
        check_url_or_raise(original_url)

        url = clean_url(original_url)
        for extractor in self.extractors:
            url = extractor.sanitize_url(url)

        result.set_url(url)
        if original_url != url:
            result.set("original_url", original_url)

        for db in self.databases:
            db.started(result)

        for extractor in self.extractors:
            try:
                extracted = extractor.download(result)
                if extracted:
                    result.merge(extracted)
                    if result.is_success():
                        break
            except Exception:
                pass

        for enricher in self.enrichers:
            try:
                enricher.enrich(result)
            except Exception:
                pass

        result.store(storages=self.storages)

        if self.formatters:
            final_media = self.formatters[0].format(result)
            if final_media:
                final_media.store(url=url, metadata=result, storages=self.storages)
                result.set_final_media(final_media)

        if result.is_empty():
            result.status = "nothing archived"

        for db in self.databases:
            try:
                db.done(result)
            except Exception:
                pass

        return result

    def cleanup(self) -> None:
        """Calls cleanup on all extractors."""
        for extractor in self.extractors:
            try:
                extractor.cleanup()
            except Exception:
                pass

    @property
    def all_modules(self) -> List[Type[BaseModule]]:
        """Returns all loaded modules."""
        return (
            self.feeders +
            self.extractors +
            self.enrichers +
            self.databases +
            self.storages +
            self.formatters
        )
