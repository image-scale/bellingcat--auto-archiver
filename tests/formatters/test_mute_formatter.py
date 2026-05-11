"""Tests for the Mute Formatter module."""

import pytest

from webkeeper.core import Metadata, Media
from webkeeper.modules.mute_formatter.mute_formatter import MuteFormatter


@pytest.fixture
def mute_formatter():
    """Create a MuteFormatter instance."""
    formatter = MuteFormatter()
    formatter.name = "mute_formatter"
    formatter.config = {}
    return formatter


class TestMuteFormatter:
    """Test the MuteFormatter functionality."""

    def test_format_returns_none(self, mute_formatter):
        """format always returns None."""
        item = Metadata().set_url("https://example.com/test")
        item.set("title", "Test Title")

        result = mute_formatter.format(item)

        assert result is None

    def test_format_with_empty_metadata(self, mute_formatter):
        """format returns None for empty metadata."""
        item = Metadata().set_url("https://example.com/empty")

        result = mute_formatter.format(item)

        assert result is None

    def test_format_with_media(self, mute_formatter):
        """format returns None even with media attached."""
        item = Metadata().set_url("https://example.com/with-media")
        item.add_media(Media(filename="test.mp4"))

        result = mute_formatter.format(item)

        assert result is None

    def test_format_does_not_modify_metadata(self, mute_formatter):
        """format does not modify the metadata object."""
        item = Metadata().set_url("https://example.com/test")
        item.set("title", "Original")

        mute_formatter.format(item)

        assert item.get("title") == "Original"
