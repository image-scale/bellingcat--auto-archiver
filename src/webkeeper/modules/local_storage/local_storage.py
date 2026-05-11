"""Local storage module for saving media files to the filesystem."""

import os
import shutil
from typing import IO

from loguru import logger

from webkeeper.core import Storage, Media, Metadata, SetupError


class LocalStorage(Storage):
    """Storage that saves media files to a local directory."""

    def setup(self) -> None:
        """Validate configuration."""
        if len(self.save_to) > 200:
            raise SetupError(
                "save_to path is too long. Please use a shorter path."
            )

    def get_cdn_url(self, media: Media) -> str:
        """Return the local path where the file is stored."""
        if self.save_absolute:
            return os.path.abspath(media.key)
        return media.key

    def set_key(self, media: Media, url: str, metadata: Metadata) -> None:
        """Generate storage key with save_to folder prefix."""
        old_folder = metadata.get_context("folder", "")
        metadata.set_context("folder", os.path.join(self.save_to, old_folder))
        super().set_key(media, url, metadata)
        metadata.set_context("folder", old_folder)

    def upload(self, media: Media, **kwargs) -> bool:
        """Copy file to local storage location."""
        dest = media.key

        os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
        logger.debug(f"[LocalStorage] copying {media.filename} to {dest}")

        shutil.copy2(media.filename, dest)
        return True

    def uploadf(self, file: IO[bytes], media: Media, **kwargs) -> bool:
        """Not used for local storage."""
        pass
