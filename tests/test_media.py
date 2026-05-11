"""Tests for the Media class."""

import pytest
from unittest.mock import Mock, patch

from webkeeper.core.media import Media


class TestMediaBasics:
    """Test basic Media properties and methods."""

    def test_media_creation_with_filename(self):
        """Media can be created with a filename."""
        media = Media(filename="video.mp4")
        assert media.filename == "video.mp4"
        assert media.urls == []
        assert media.properties == {}

    def test_media_key_property(self):
        """Media key property returns _key value."""
        media = Media(filename="test.mp4", _key="my/path")
        assert media.key == "my/path"

    def test_media_set_returns_self(self):
        """Media.set returns self for method chaining."""
        media = Media(filename="test.mp4")
        result = media.set("author", "John")
        assert result is media

    def test_media_get_returns_value(self):
        """Media.get retrieves property values."""
        media = Media(filename="test.mp4")
        media.set("author", "John")
        assert media.get("author") == "John"

    def test_media_get_returns_default(self):
        """Media.get returns default for missing keys."""
        media = Media(filename="test.mp4")
        assert media.get("nonexistent") is None
        assert media.get("nonexistent", "default") == "default"

    def test_media_add_url(self):
        """Media.add_url adds URLs to the list."""
        media = Media(filename="test.mp4")
        media.add_url("https://cdn.example.com/test.mp4")
        assert "https://cdn.example.com/test.mp4" in media.urls
        media.add_url("https://backup.example.com/test.mp4")
        assert len(media.urls) == 2


class TestMediaMimetype:
    """Test mimetype detection and handling."""

    @pytest.mark.parametrize("filename,expected", [
        ("video.mp4", "video/mp4"),
        ("image.jpg", "image/jpeg"),
        ("image.png", "image/png"),
        ("audio.mp3", "audio/mpeg"),
        ("document.pdf", "application/pdf"),
        ("text.txt", "text/plain"),
    ])
    def test_mimetype_detection(self, filename, expected):
        """Mimetype is correctly detected from filename extension."""
        media = Media(filename=filename)
        assert media.mimetype == expected

    def test_mimetype_setter(self):
        """Mimetype can be set explicitly."""
        media = Media(filename="file.unknown")
        media.mimetype = "custom/type"
        assert media.mimetype == "custom/type"

    def test_mimetype_empty_filename(self):
        """Empty filename returns empty mimetype."""
        media = Media(filename="")
        assert media.mimetype == ""


class TestMediaTypeChecks:
    """Test media type checking methods."""

    @pytest.mark.parametrize("filename,is_video,is_audio,is_image", [
        ("video.mp4", True, False, False),
        ("video.avi", True, False, False),
        ("audio.mp3", False, True, False),
        ("audio.wav", False, True, False),
        ("image.jpg", False, False, True),
        ("image.png", False, False, True),
        ("document.pdf", False, False, False),
    ])
    def test_type_checks(self, filename, is_video, is_audio, is_image):
        """Media type check methods work correctly."""
        media = Media(filename=filename)
        assert media.is_video() == is_video
        assert media.is_audio() == is_audio
        assert media.is_image() == is_image


class TestMediaInnerMedia:
    """Test nested media retrieval."""

    def test_all_inner_media_no_nested(self):
        """all_inner_media yields nothing when no nested media."""
        media = Media(filename="test.mp4")
        inner = list(media.all_inner_media(include_self=False))
        assert len(inner) == 0

    def test_all_inner_media_with_self(self):
        """all_inner_media includes self when requested."""
        media = Media(filename="test.mp4")
        inner = list(media.all_inner_media(include_self=True))
        assert len(inner) == 1
        assert inner[0] is media

    def test_all_inner_media_with_nested(self):
        """all_inner_media yields nested Media objects."""
        parent = Media(filename="parent.mp4")
        child = Media(filename="child.jpg")
        grandchild = Media(filename="grandchild.png")

        child.set("thumbnail", grandchild)
        parent.set("preview", child)

        inner = list(parent.all_inner_media(include_self=False))
        assert len(inner) == 2
        assert child in inner
        assert grandchild in inner

    def test_all_inner_media_with_list_property(self):
        """all_inner_media handles lists of Media objects."""
        parent = Media(filename="parent.mp4")
        frame1 = Media(filename="frame1.jpg")
        frame2 = Media(filename="frame2.jpg")

        parent.set("frames", [frame1, frame2])

        inner = list(parent.all_inner_media(include_self=False))
        assert len(inner) == 2
        assert frame1 in inner
        assert frame2 in inner


class TestMediaIsStored:
    """Test the is_stored method."""

    def test_is_stored_no_urls(self):
        """Media without URLs is not stored."""
        media = Media(filename="test.mp4")
        storage = Mock()
        storage.config = {"steps": {"storages": ["s3", "local"]}}
        assert media.is_stored(storage) is False

    def test_is_stored_partial_urls(self):
        """Media with fewer URLs than storages is not fully stored."""
        media = Media(filename="test.mp4")
        media.add_url("https://s3.example.com/test.mp4")
        storage = Mock()
        storage.config = {"steps": {"storages": ["s3", "local"]}}
        assert media.is_stored(storage) is False

    def test_is_stored_full_urls(self):
        """Media with URLs matching storage count is stored."""
        media = Media(filename="test.mp4")
        media.add_url("https://s3.example.com/test.mp4")
        media.add_url("file:///local/test.mp4")
        storage = Mock()
        storage.config = {"steps": {"storages": ["s3", "local"]}}
        assert media.is_stored(storage) is True


class TestMediaStore:
    """Test media storage functionality."""

    def test_store_with_no_storages(self):
        """Store with empty storages does nothing."""
        media = Media(filename="test.mp4")
        metadata = Mock()
        media.store(metadata, storages=[])

    def test_store_with_storage(self):
        """Store calls storage.store for each inner media."""
        media = Media(filename="test.mp4")
        metadata = Mock()
        mock_storage = Mock()
        media.store(metadata, url="https://example.com", storages=[mock_storage])
        mock_storage.store.assert_called_once()


class TestMediaValidVideo:
    """Test video validation functionality."""

    def test_is_valid_video_with_valid_probe(self):
        """Valid video with duration returns True."""
        media = Media(filename="test.mp4")
        mock_streams = {"streams": [{"duration_ts": 1000}]}

        with patch("ffmpeg.probe", return_value=mock_streams):
            assert media.is_valid_video() is True

    def test_is_valid_video_with_no_duration(self):
        """Video with zero duration returns False."""
        media = Media(filename="test.mp4")
        mock_streams = {"streams": [{"duration_ts": 0}]}

        with patch("ffmpeg.probe", return_value=mock_streams):
            assert media.is_valid_video() is False
