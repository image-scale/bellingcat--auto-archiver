"""Tests for the orchestrator."""

import pytest
import os

from webkeeper.core.orchestrator import Orchestrator, clean_url, check_url_or_raise
from webkeeper.core import Metadata, Media, SetupError


FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures", "modules")


@pytest.fixture
def basic_config():
    """Config with all sample modules."""
    return {
        "module_paths": [FIXTURES_DIR],
        "steps": {
            "feeders": ["sample_feeder"],
            "extractors": ["sample_extractor"],
            "enrichers": ["sample_enricher"],
            "databases": ["sample_database"],
            "storages": ["sample_storage"],
            "formatters": ["sample_formatter"],
        },
        "sample_feeder": {"urls": ["https://example.com/test"]},
    }


class TestCleanUrl:
    """Test URL cleaning utility."""

    def test_removes_utm_params(self):
        """clean_url removes tracking parameters."""
        url = "https://example.com/page?utm_source=test&utm_medium=email&real=keep"
        result = clean_url(url)
        assert "utm_source" not in result
        assert "utm_medium" not in result
        assert "real=keep" in result

    def test_removes_fbclid(self):
        """clean_url removes fbclid."""
        url = "https://example.com/page?fbclid=abc123&data=keep"
        result = clean_url(url)
        assert "fbclid" not in result
        assert "data=keep" in result

    def test_preserves_clean_url(self):
        """clean_url preserves URLs without tracking."""
        url = "https://example.com/page?id=123&type=video"
        result = clean_url(url)
        assert result == url


class TestCheckUrlOrRaise:
    """Test URL validation."""

    def test_valid_http_url(self):
        """Valid HTTP URLs pass."""
        assert check_url_or_raise("http://example.com") is True

    def test_valid_https_url(self):
        """Valid HTTPS URLs pass."""
        assert check_url_or_raise("https://example.com/path") is True

    def test_invalid_scheme_raises(self):
        """Non-HTTP schemes raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            check_url_or_raise("ftp://example.com")
        assert "Invalid URL scheme" in str(exc_info.value)

    def test_localhost_raises(self):
        """Localhost URLs raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            check_url_or_raise("http://localhost/test")
        assert "Localhost" in str(exc_info.value)

    def test_missing_hostname_raises(self):
        """URLs without hostname raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            check_url_or_raise("http:///path")
        assert "Invalid URL hostname" in str(exc_info.value)


class TestOrchestratorSetup:
    """Test orchestrator initialization."""

    def test_orchestrator_creation(self):
        """Orchestrator can be created."""
        orch = Orchestrator()
        assert orch.feeders == []
        assert orch.extractors == []
        assert orch.setup_finished is False

    def test_setup_loads_modules(self, basic_config):
        """setup loads configured modules."""
        orch = Orchestrator()
        orch.setup(basic_config)

        assert len(orch.feeders) == 1
        assert len(orch.extractors) == 1
        assert len(orch.enrichers) == 1
        assert len(orch.databases) == 1
        assert len(orch.storages) == 1
        assert len(orch.formatters) == 1
        assert orch.setup_finished is True

    def test_setup_only_runs_once(self, basic_config):
        """setup only runs once."""
        orch = Orchestrator()
        orch.setup(basic_config)
        original_feeders = orch.feeders

        orch.setup(basic_config)

        assert orch.feeders is original_feeders

    def test_setup_with_missing_module_raises(self):
        """setup raises SetupError for missing module."""
        config = {
            "module_paths": [FIXTURES_DIR],
            "steps": {"feeders": ["nonexistent_module"]},
        }

        orch = Orchestrator()
        with pytest.raises(SetupError):
            orch.setup(config)


class TestOrchestratorFeed:
    """Test feed processing."""

    def test_feed_processes_urls(self, basic_config):
        """feed processes URLs from feeders."""
        orch = Orchestrator()
        orch.setup(basic_config)

        results = list(orch.feed())

        assert len(results) == 1
        assert results[0].get_url() == "https://example.com/test"

    def test_feed_notifies_database_started(self, basic_config):
        """feed notifies database when archiving starts."""
        orch = Orchestrator()
        orch.setup(basic_config)

        list(orch.feed())

        db = orch.databases[0]
        assert len(db.started_items) == 1

    def test_feed_notifies_database_done(self, basic_config):
        """feed notifies database when archiving completes."""
        orch = Orchestrator()
        orch.setup(basic_config)

        list(orch.feed())

        db = orch.databases[0]
        assert len(db.done_items) == 1


class TestOrchestratorArchive:
    """Test archive method."""

    def test_archive_runs_extractor(self, basic_config):
        """archive runs extractor on item."""
        orch = Orchestrator()
        orch.setup(basic_config)

        item = Metadata().set_url("https://example.com/video")
        result = orch.feed_item(item)

        assert result.is_success()

    def test_archive_runs_enricher(self, basic_config):
        """archive runs enricher on result."""
        orch = Orchestrator()
        orch.setup(basic_config)

        item = Metadata().set_url("https://example.com/video")
        result = orch.feed_item(item)

        assert result.get("enriched") is True

    def test_archive_stores_media(self, basic_config):
        """archive stores media via storage."""
        orch = Orchestrator()
        orch.setup(basic_config)

        item = Metadata().set_url("https://example.com/video")
        result = orch.feed_item(item)

        storage = orch.storages[0]
        assert len(storage.uploads) > 0

    def test_archive_cleans_tracking_params(self, basic_config):
        """archive removes tracking parameters from URL."""
        orch = Orchestrator()
        orch.setup(basic_config)

        item = Metadata().set_url("https://example.com/video?utm_source=test")
        result = orch.feed_item(item)

        assert "utm_source" not in result.get_url()

    def test_archive_preserves_original_url(self, basic_config):
        """archive preserves original URL when sanitized."""
        orch = Orchestrator()
        orch.setup(basic_config)

        item = Metadata().set_url("https://example.com/video?utm_source=test")
        result = orch.feed_item(item)

        assert result.get("original_url") == "https://example.com/video?utm_source=test"

    def test_archive_invalid_url_fails(self, basic_config):
        """archive fails for invalid URLs."""
        orch = Orchestrator()
        orch.setup(basic_config)

        item = Metadata().set_url("not-a-valid-url")
        result = orch.feed_item(item)

        assert result is None
        db = orch.databases[0]
        assert len(db.failed_items) == 1


class TestOrchestratorCleanup:
    """Test cleanup functionality."""

    def test_cleanup_calls_extractor_cleanup(self, basic_config):
        """cleanup calls cleanup on extractors."""
        orch = Orchestrator()
        orch.setup(basic_config)

        orch.cleanup()

        extractor = orch.extractors[0]
        assert hasattr(extractor, 'cleaned_up')
        assert extractor.cleaned_up is True

    def test_feed_calls_cleanup_after_processing(self, basic_config):
        """feed calls cleanup after processing all items."""
        orch = Orchestrator()
        orch.setup(basic_config)

        list(orch.feed())

        extractor = orch.extractors[0]
        assert extractor.cleaned_up is True


class TestOrchestratorAllModules:
    """Test all_modules property."""

    def test_all_modules_returns_all(self, basic_config):
        """all_modules returns all loaded modules."""
        orch = Orchestrator()
        orch.setup(basic_config)

        all_mods = orch.all_modules

        assert len(all_mods) == 6
