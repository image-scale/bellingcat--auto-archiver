"""Tests for the base module system."""

import pytest
from unittest.mock import Mock, patch
import os
import tempfile

from webkeeper.core.base_module import BaseModule, MODULE_TYPES, SetupError
from webkeeper.core.feeder import Feeder
from webkeeper.core.extractor import Extractor
from webkeeper.core.enricher import Enricher
from webkeeper.core.database import Database
from webkeeper.core.storage import Storage
from webkeeper.core.formatter import Formatter
from webkeeper.core.metadata import Metadata
from webkeeper.core.media import Media


class TestBaseModule:
    """Test BaseModule functionality."""

    def test_module_types_constant(self):
        """MODULE_TYPES contains all module types."""
        assert "feeder" in MODULE_TYPES
        assert "extractor" in MODULE_TYPES
        assert "enricher" in MODULE_TYPES
        assert "database" in MODULE_TYPES
        assert "storage" in MODULE_TYPES
        assert "formatter" in MODULE_TYPES
        assert len(MODULE_TYPES) == 6

    def test_config_setup_stores_config(self):
        """config_setup stores config on module."""
        class TestModule(BaseModule):
            pass

        module = TestModule()
        module.name = "test_module"
        config = {"test_module": {"setting1": "value1"}, "other": "data"}

        module.config_setup(config)

        assert module.config is not None
        assert "other" in module.config

    def test_config_setup_sets_module_attributes(self):
        """config_setup sets module-specific settings as attributes."""
        class TestModule(BaseModule):
            pass

        module = TestModule()
        module.name = "test_module"
        config = {"test_module": {"api_key": "secret123", "timeout": 30}}

        module.config_setup(config)

        assert module.api_key == "secret123"
        assert module.timeout == 30

    def test_config_setup_stores_authentication(self):
        """config_setup extracts authentication into separate dict."""
        class TestModule(BaseModule):
            pass

        module = TestModule()
        module.name = "test_module"
        config = {
            "test_module": {},
            "authentication": {"twitter.com": {"api_key": "key123"}}
        }

        module.config_setup(config)

        assert module.authentication == {"twitter.com": {"api_key": "key123"}}

    def test_auth_for_site_finds_domain(self):
        """auth_for_site retrieves auth for a domain."""
        class TestModule(BaseModule):
            pass

        module = TestModule()
        module.name = "test"
        module.authentication = {
            "twitter.com": {"api_key": "key123", "api_secret": "secret"}
        }

        auth = module.auth_for_site("https://twitter.com/user/status/123")
        assert auth["api_key"] == "key123"
        assert auth["api_secret"] == "secret"

    def test_auth_for_site_strips_www(self):
        """auth_for_site finds auth when domain has www prefix."""
        class TestModule(BaseModule):
            pass

        module = TestModule()
        module.name = "test"
        module.authentication = {"example.com": {"token": "abc"}}

        auth = module.auth_for_site("https://www.example.com/page")
        assert auth["token"] == "abc"

    def test_auth_for_site_returns_empty_when_not_found(self):
        """auth_for_site returns empty dict when no auth configured."""
        class TestModule(BaseModule):
            pass

        module = TestModule()
        module.name = "test"
        module.authentication = {}

        auth = module.auth_for_site("https://unknown.com")
        assert auth == {}

    def test_setup_can_be_overridden(self):
        """setup method can be overridden in subclasses."""
        class CustomModule(BaseModule):
            def setup(self):
                self.initialized = True

        module = CustomModule()
        module.setup()
        assert module.initialized is True

    def test_storages_property(self):
        """storages property returns configured storages."""
        class TestModule(BaseModule):
            pass

        module = TestModule()
        module.config = {"storages": ["local", "s3"]}

        assert module.storages == ["local", "s3"]

    def test_storages_property_empty_default(self):
        """storages property returns empty list when not configured."""
        class TestModule(BaseModule):
            pass

        module = TestModule()
        module.config = {}

        assert module.storages == []


class TestFeeder:
    """Test Feeder base class."""

    def test_feeder_is_abstract(self):
        """Feeder cannot be instantiated without implementing __iter__."""
        with pytest.raises(TypeError):
            Feeder()

    def test_feeder_iter_returns_metadata(self):
        """Feeder __iter__ should yield Metadata objects."""
        class TestFeeder(Feeder):
            def __iter__(self):
                yield Metadata().set_url("https://example.com/1")
                yield Metadata().set_url("https://example.com/2")

        feeder = TestFeeder()
        items = list(feeder)

        assert len(items) == 2
        assert all(isinstance(item, Metadata) for item in items)
        assert items[0].get_url() == "https://example.com/1"


class TestExtractor:
    """Test Extractor base class."""

    def test_extractor_is_abstract(self):
        """Extractor cannot be instantiated without implementing download."""
        with pytest.raises(TypeError):
            Extractor()

    def test_sanitize_url_default_returns_unchanged(self):
        """Default sanitize_url returns URL unchanged."""
        class TestExtractor(Extractor):
            def download(self, item):
                return item

        extractor = TestExtractor()
        url = "https://example.com/page?utm_source=test"

        assert extractor.sanitize_url(url) == url

    def test_suitable_returns_true_by_default(self):
        """suitable returns True when no valid_url pattern."""
        class TestExtractor(Extractor):
            def download(self, item):
                return item

        extractor = TestExtractor()
        assert extractor.suitable("https://anything.com") is True

    def test_suitable_uses_valid_url_pattern(self):
        """suitable uses valid_url pattern when defined."""
        import re

        class TwitterExtractor(Extractor):
            valid_url = re.compile(r"https?://(?:www\.)?twitter\.com/.*")

            def download(self, item):
                return item

        extractor = TwitterExtractor()
        assert extractor.suitable("https://twitter.com/user/status/123") is True
        assert extractor.suitable("https://facebook.com/post") is False

    def test_cleanup_default_does_nothing(self):
        """Default cleanup method does nothing."""
        class TestExtractor(Extractor):
            def download(self, item):
                return item

        extractor = TestExtractor()
        extractor.cleanup()

    def test_guess_file_type(self):
        """_guess_file_type returns general media type."""
        class TestExtractor(Extractor):
            def download(self, item):
                return item

        extractor = TestExtractor()

        assert extractor._guess_file_type("video.mp4") == "video"
        assert extractor._guess_file_type("image.jpg") == "image"
        assert extractor._guess_file_type("audio.mp3") == "audio"


class TestEnricher:
    """Test Enricher base class."""

    def test_enricher_is_abstract(self):
        """Enricher cannot be instantiated without implementing enrich."""
        with pytest.raises(TypeError):
            Enricher()

    def test_enrich_modifies_metadata(self):
        """enrich can modify Metadata in place."""
        class HashEnricher(Enricher):
            def enrich(self, to_enrich):
                to_enrich.set("hash", "abc123")

        enricher = HashEnricher()
        metadata = Metadata().set_url("https://example.com")

        enricher.enrich(metadata)

        assert metadata.get("hash") == "abc123"


class TestDatabase:
    """Test Database base class."""

    def test_database_is_abstract(self):
        """Database cannot be instantiated without implementing done."""
        with pytest.raises(TypeError):
            Database()

    def test_started_default_does_nothing(self):
        """Default started method does nothing."""
        class TestDb(Database):
            def done(self, item, cached=False):
                pass

        db = TestDb()
        db.started(Metadata())

    def test_failed_default_does_nothing(self):
        """Default failed method does nothing."""
        class TestDb(Database):
            def done(self, item, cached=False):
                pass

        db = TestDb()
        db.failed(Metadata(), "error")

    def test_aborted_default_does_nothing(self):
        """Default aborted method does nothing."""
        class TestDb(Database):
            def done(self, item, cached=False):
                pass

        db = TestDb()
        db.aborted(Metadata())

    def test_fetch_default_returns_false(self):
        """Default fetch returns False."""
        class TestDb(Database):
            def done(self, item, cached=False):
                pass

        db = TestDb()
        assert db.fetch(Metadata()) is False

    def test_done_receives_metadata(self):
        """done method receives Metadata and cached flag."""
        class TrackingDb(Database):
            def __init__(self):
                self.done_calls = []

            def done(self, item, cached=False):
                self.done_calls.append((item, cached))

        db = TrackingDb()
        metadata = Metadata().set_url("https://example.com")
        metadata.success()

        db.done(metadata, cached=False)

        assert len(db.done_calls) == 1
        assert db.done_calls[0][0] is metadata
        assert db.done_calls[0][1] is False


class TestStorage:
    """Test Storage base class."""

    def test_storage_is_abstract(self):
        """Storage cannot be instantiated without implementing abstract methods."""
        with pytest.raises(TypeError):
            Storage()

    def test_set_key_flat_generator(self, tmp_path):
        """set_key with flat path_generator puts file in root."""
        class TestStorage(Storage):
            path_generator = "flat"
            filename_generator = "random"

            def get_cdn_url(self, media):
                return f"http://cdn.com/{media.key}"

            def uploadf(self, file, media, **kwargs):
                return True

        storage = TestStorage()

        src_file = tmp_path / "test.txt"
        src_file.write_text("content")
        media = Media(filename=str(src_file))

        storage.set_key(media, "https://example.com", Metadata())

        assert "/" not in media.key.rstrip("/") or media.key.count("/") <= 1

    def test_set_key_url_generator(self, tmp_path):
        """set_key with url path_generator creates URL-based path."""
        class TestStorage(Storage):
            path_generator = "url"
            filename_generator = "random"

            def get_cdn_url(self, media):
                return f"http://cdn.com/{media.key}"

            def uploadf(self, file, media, **kwargs):
                return True

        storage = TestStorage()

        src_file = tmp_path / "test.txt"
        src_file.write_text("content")
        media = Media(filename=str(src_file))

        storage.set_key(media, "https://example.com/page/123", Metadata())

        assert "example" in media.key

    def test_set_key_preserves_existing(self, tmp_path):
        """set_key does not overwrite existing key."""
        class TestStorage(Storage):
            path_generator = "flat"
            filename_generator = "random"

            def get_cdn_url(self, media):
                return f"http://cdn.com/{media.key}"

            def uploadf(self, file, media, **kwargs):
                return True

        storage = TestStorage()
        media = Media(filename="test.txt", _key="existing/key.txt")

        storage.set_key(media, "https://example.com", Metadata())

        assert media.key == "existing/key.txt"

    def test_store_calls_upload(self, tmp_path):
        """store method coordinates key generation and upload."""
        class TrackingStorage(Storage):
            path_generator = "flat"
            filename_generator = "random"

            def __init__(self):
                self.uploads = []

            def get_cdn_url(self, media):
                return f"http://cdn.com/{media.key}"

            def uploadf(self, file, media, **kwargs):
                self.uploads.append(media.key)
                return True

        storage = TrackingStorage()
        storage.config = {"steps": {"storages": []}}

        src_file = tmp_path / "test.txt"
        src_file.write_text("content")
        media = Media(filename=str(src_file))

        storage.store(media, "https://example.com", Metadata())

        assert len(storage.uploads) == 1
        assert len(media.urls) == 1


class TestFormatter:
    """Test Formatter base class."""

    def test_formatter_is_abstract(self):
        """Formatter cannot be instantiated without implementing format."""
        with pytest.raises(TypeError):
            Formatter()

    def test_format_returns_media(self):
        """format method returns a Media object."""
        class HtmlFormatter(Formatter):
            def format(self, item):
                return Media(filename="report.html")

        formatter = HtmlFormatter()
        metadata = Metadata().set_url("https://example.com")

        result = formatter.format(metadata)

        assert isinstance(result, Media)
        assert result.filename == "report.html"

    def test_format_can_return_none(self):
        """format method can return None (mute formatter)."""
        class MuteFormatter(Formatter):
            def format(self, item):
                return None

        formatter = MuteFormatter()
        result = formatter.format(Metadata())

        assert result is None


class TestSetupError:
    """Test SetupError exception."""

    def test_setup_error_is_exception(self):
        """SetupError is a valid exception."""
        with pytest.raises(SetupError):
            raise SetupError("Configuration error")

    def test_setup_error_message(self):
        """SetupError preserves message."""
        try:
            raise SetupError("Missing API key")
        except SetupError as e:
            assert "Missing API key" in str(e)
