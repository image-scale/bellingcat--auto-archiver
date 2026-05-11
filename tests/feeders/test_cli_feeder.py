"""Tests for the CLI Feeder module."""

import pytest

from webkeeper.core import Metadata, SetupError
from webkeeper.modules.cli_feeder.cli_feeder import CLIFeeder


@pytest.fixture
def cli_feeder():
    """Create a CLIFeeder instance with custom config."""
    def _create(urls):
        feeder = CLIFeeder()
        feeder.config = {"urls": urls}
        feeder.name = "cli_feeder"
        feeder.tmp_dir = "/tmp"
        return feeder
    return _create


class TestCLIFeederIteration:
    """Test CLI feeder iteration."""

    def test_yields_metadata_for_each_url(self, cli_feeder):
        """Iteration yields Metadata objects for each URL."""
        urls = ["https://example.com/1", "https://example.com/2", "https://example.com/3"]
        feeder = cli_feeder(urls)
        feeder.setup()

        items = list(feeder)

        assert len(items) == 3
        assert all(isinstance(item, Metadata) for item in items)
        assert items[0].get_url() == "https://example.com/1"
        assert items[1].get_url() == "https://example.com/2"
        assert items[2].get_url() == "https://example.com/3"

    def test_single_url(self, cli_feeder):
        """Single URL yields one Metadata object."""
        feeder = cli_feeder(["https://example.com/single"])
        feeder.setup()

        items = list(feeder)

        assert len(items) == 1
        assert items[0].get_url() == "https://example.com/single"

    def test_preserves_url_order(self, cli_feeder):
        """URLs are yielded in the order provided."""
        urls = ["https://z.com", "https://a.com", "https://m.com"]
        feeder = cli_feeder(urls)
        feeder.setup()

        items = list(feeder)

        assert [item.get_url() for item in items] == urls


class TestCLIFeederSetup:
    """Test CLI feeder setup validation."""

    def test_setup_raises_on_empty_urls(self, cli_feeder):
        """Setup raises SetupError when URLs list is empty."""
        feeder = cli_feeder([])

        with pytest.raises(SetupError) as exc_info:
            feeder.setup()

        assert "No URLs provided" in str(exc_info.value)

    def test_setup_raises_on_none_urls(self, cli_feeder):
        """Setup raises SetupError when urls is None."""
        feeder = cli_feeder(None)

        with pytest.raises(SetupError) as exc_info:
            feeder.setup()

        assert "No URLs provided" in str(exc_info.value)

    def test_setup_stores_urls(self, cli_feeder):
        """Setup stores URLs for iteration."""
        urls = ["https://example.com/test"]
        feeder = cli_feeder(urls)

        feeder.setup()

        assert feeder.urls == urls


class TestCLIFeederReusability:
    """Test that feeder can be iterated multiple times."""

    def test_multiple_iterations(self, cli_feeder):
        """Feeder can be iterated multiple times."""
        feeder = cli_feeder(["https://example.com/1", "https://example.com/2"])
        feeder.setup()

        first = list(feeder)
        second = list(feeder)

        assert len(first) == 2
        assert len(second) == 2
        assert first[0].get_url() == second[0].get_url()
