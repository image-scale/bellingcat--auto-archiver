"""Tests for the Local Storage module."""

import os
from pathlib import Path

import pytest

from webkeeper.core import Media, Metadata, SetupError
from webkeeper.modules.local_storage.local_storage import LocalStorage


@pytest.fixture
def local_storage(tmp_path):
    """Create a LocalStorage instance with temp directory."""
    save_to = tmp_path / "local_archive"
    save_to.mkdir()

    storage = LocalStorage()
    storage.name = "local_storage"
    storage.config = {
        "path_generator": "flat",
        "filename_generator": "static",
        "save_to": str(save_to),
        "save_absolute": False,
    }
    storage.path_generator = "flat"
    storage.filename_generator = "static"
    storage.save_to = str(save_to)
    storage.save_absolute = False
    return storage


@pytest.fixture
def sample_media(tmp_path):
    """Create a Media object with a temporary source file."""
    src_file = tmp_path / "source.txt"
    src_file.write_text("test content")
    return Media(filename=str(src_file))


class TestLocalStorageSetup:
    """Test local storage setup validation."""

    def test_setup_rejects_long_path(self, tmp_path):
        """Setup raises SetupError for paths over 200 chars."""
        storage = LocalStorage()
        storage.save_to = "long" * 100  # 400 chars

        with pytest.raises(SetupError):
            storage.setup()

    def test_setup_accepts_normal_path(self, local_storage):
        """Setup accepts paths under 200 chars."""
        local_storage.setup()  # Should not raise


class TestLocalStorageCdnUrl:
    """Test CDN URL generation."""

    def test_get_cdn_url_relative(self, local_storage):
        """get_cdn_url returns the key path by default."""
        media = Media(filename="dummy.txt")
        local_storage.filename_generator = "random"
        local_storage.set_key(media, "https://example.com", Metadata())

        result = local_storage.get_cdn_url(media)

        assert result == media.key

    def test_get_cdn_url_absolute(self, local_storage):
        """get_cdn_url returns absolute path when save_absolute is True."""
        media = Media(filename="dummy.txt")
        local_storage.filename_generator = "random"
        local_storage.save_absolute = True
        local_storage.set_key(media, "https://example.com", Metadata())

        result = local_storage.get_cdn_url(media)

        assert os.path.isabs(result)


class TestLocalStorageUpload:
    """Test file upload functionality."""

    def test_upload_copies_file(self, local_storage, sample_media):
        """upload copies file to destination."""
        local_storage.store(sample_media, "https://example.com", Metadata())
        dest = sample_media.key

        assert os.path.exists(dest)
        assert Path(dest).read_text() == Path(sample_media.filename).read_text()

    def test_upload_preserves_content(self, local_storage, sample_media):
        """upload preserves file content."""
        original_content = Path(sample_media.filename).read_text()
        local_storage.store(sample_media, "https://example.com", Metadata())

        stored_content = Path(sample_media.key).read_text()
        assert stored_content == original_content

    def test_upload_nonexistent_file_raises(self, local_storage):
        """upload raises FileNotFoundError for missing file."""
        media = Media(filename="nonexistent.txt")
        media._key = "dest.txt"

        with pytest.raises(FileNotFoundError):
            local_storage.upload(media)


class TestLocalStorageKeyGeneration:
    """Test storage key generation."""

    def test_set_key_uses_save_to_folder(self, local_storage, sample_media):
        """set_key prepends save_to folder to key."""
        local_storage.set_key(sample_media, "https://example.com", Metadata())

        assert sample_media.key.startswith(local_storage.save_to)
