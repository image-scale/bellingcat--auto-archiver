"""
Storage base module for persisting archived media files.

Storages handle uploading media files to various destinations (local
filesystem, S3, Google Drive, etc.) and tracking where files are stored.
"""

from __future__ import annotations
from abc import abstractmethod
import os
import uuid
from typing import Any, IO

from slugify import slugify

from .base_module import BaseModule
from .media import Media
from .metadata import Metadata


def random_str(length: int = 32) -> str:
    """Generates a random string for filenames/paths."""
    assert length <= 32, "length must be less than 32"
    return str(uuid.uuid4()).replace("-", "")[:length]


class Storage(BaseModule):
    """
    Base class for storage modules.

    Storages persist media files and track their locations. They support
    configurable path and filename generation strategies.

    Attributes:
        path_generator: Strategy for directory structure ('flat', 'url', 'random')
        filename_generator: Strategy for filenames ('random', 'static')
    """

    def store(self, media: Media, url: str, metadata: Metadata = None) -> None:
        """
        Stores a media file.

        Generates a storage key, uploads the file, and records the CDN URL.

        Args:
            media: Media object to store
            url: Original URL being archived
            metadata: Associated Metadata object
        """
        if media.is_stored(in_storage=self):
            return

        self.set_key(media, url, metadata)
        self.upload(media, metadata=metadata)
        media.add_url(self.get_cdn_url(media))

    @abstractmethod
    def get_cdn_url(self, media: Media) -> str:
        """
        Returns the URL where stored media can be accessed.

        Args:
            media: Stored Media object

        Returns:
            URL to access the stored file
        """
        pass

    @abstractmethod
    def uploadf(self, file: IO[bytes], media: Media, **kwargs: dict) -> bool:
        """
        Uploads a file to storage.

        Args:
            file: Open file handle to upload
            media: Media object being stored
            **kwargs: Additional storage-specific options

        Returns:
            True on success, False on failure
        """
        pass

    def upload(self, media: Media, **kwargs) -> bool:
        """
        Opens file and calls uploadf.

        Args:
            media: Media object to upload
            **kwargs: Passed to uploadf

        Returns:
            Result of uploadf
        """
        with open(media.filename, "rb") as f:
            return self.uploadf(f, media, **kwargs)

    def set_key(self, media: Media, url: str, metadata: Metadata) -> None:
        """
        Generates and sets the storage key for a media file.

        Uses configured path_generator and filename_generator strategies.

        Args:
            media: Media object to set key on
            url: Original URL
            metadata: Associated Metadata
        """
        if media.key is not None and len(media.key) > 0:
            return

        folder = ""
        if metadata:
            folder = metadata.get_context("folder", "")

        _, ext = os.path.splitext(media.filename)

        path_gen = getattr(self, 'path_generator', 'flat')
        if path_gen == "flat":
            path = ""
        elif path_gen == "url":
            path = slugify(url)[:70]
        elif path_gen == "random":
            path = random_str(24)
        else:
            path = ""

        filename_gen = getattr(self, 'filename_generator', 'random')
        if filename_gen == "random":
            filename = random_str(24)
        elif filename_gen == "static":
            filename = self._calculate_hash(media.filename)[:24]
        else:
            filename = random_str(24)

        key = os.path.join(folder, path, f"{filename}{ext}")
        media._key = key

    def _calculate_hash(self, filepath: str) -> str:
        """Calculates SHA-256 hash of a file."""
        import hashlib
        sha = hashlib.sha256()
        with open(filepath, "rb") as f:
            while chunk := f.read(8192):
                sha.update(chunk)
        return sha.hexdigest()
