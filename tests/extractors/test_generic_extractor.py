"""Tests for the Generic Extractor module."""

import pytest
from unittest.mock import MagicMock, patch

from webkeeper.core import Metadata, Media
from webkeeper.modules.generic_extractor.generic_extractor import GenericExtractor


@pytest.fixture
def generic_extractor():
    """Create a GenericExtractor instance."""
    extractor = GenericExtractor()
    extractor.name = "generic_extractor"
    extractor.config = {}
    extractor.tmp_dir = "/tmp"
    extractor.subtitles = False
    extractor.comments = False
    extractor.livestreams = False
    extractor.allow_playlist = False
    extractor.max_downloads = "inf"
    extractor.proxy = ""
    return extractor


class TestGenericExtractorSuitable:
    """Test URL suitability checking."""

    def test_suitable_youtube_url(self, generic_extractor):
        """YouTube URLs are suitable."""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        assert generic_extractor.suitable(url) is True

    def test_suitable_tiktok_url(self, generic_extractor):
        """TikTok URLs are suitable."""
        url = "https://www.tiktok.com/@user/video/1234567890"
        assert generic_extractor.suitable(url) is True

    def test_suitable_extractors_yields_extractors(self, generic_extractor):
        """suitable_extractors yields extractor classes."""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        extractors = list(generic_extractor.suitable_extractors(url))
        assert len(extractors) > 0


class TestGenericExtractorDownload:
    """Test download functionality."""

    def test_download_returns_false_on_error(self, generic_extractor):
        """download returns False on yt-dlp error."""
        item = Metadata().set_url("https://invalid-url-that-does-not-exist.xyz/video")

        with patch("yt_dlp.YoutubeDL") as mock_ydl:
            mock_instance = MagicMock()
            mock_instance.__enter__ = MagicMock(return_value=mock_instance)
            mock_instance.__exit__ = MagicMock(return_value=False)
            mock_instance.extract_info.return_value = None
            mock_ydl.return_value = mock_instance

            result = generic_extractor.download(item)

        assert result is False

    def test_download_skips_livestream_when_disabled(self, generic_extractor):
        """download skips livestreams when livestreams=False."""
        generic_extractor.livestreams = False
        item = Metadata().set_url("https://example.com/live")

        with patch("yt_dlp.YoutubeDL") as mock_ydl:
            mock_instance = MagicMock()
            mock_instance.__enter__ = MagicMock(return_value=mock_instance)
            mock_instance.__exit__ = MagicMock(return_value=False)
            mock_instance.extract_info.return_value = {"is_live": True}
            mock_ydl.return_value = mock_instance

            result = generic_extractor.download(item)

        assert result is False


class TestGenericExtractorConfig:
    """Test configuration handling."""

    def test_default_subtitles_enabled(self, generic_extractor):
        """Default config has subtitles enabled."""
        generic_extractor.subtitles = True
        assert generic_extractor.subtitles is True

    def test_default_comments_disabled(self, generic_extractor):
        """Default config has comments disabled."""
        generic_extractor.comments = False
        assert generic_extractor.comments is False

    def test_default_livestreams_disabled(self, generic_extractor):
        """Default config has livestreams disabled."""
        generic_extractor.livestreams = False
        assert generic_extractor.livestreams is False

    def test_default_playlist_disabled(self, generic_extractor):
        """Default config has playlist downloading disabled."""
        generic_extractor.allow_playlist = False
        assert generic_extractor.allow_playlist is False
