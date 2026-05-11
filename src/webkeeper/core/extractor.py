"""
Extractor base module for downloading content from URLs.

Extractors are responsible for downloading media content from web pages
and returning the results as Metadata objects. They can sanitize URLs,
check if they support a given URL, and perform the actual download.
"""

from __future__ import annotations
from abc import abstractmethod
import mimetypes
import os
import re
from contextlib import suppress
from typing import Union

import requests
from retrying import retry

from .base_module import BaseModule
from .metadata import Metadata


class Extractor(BaseModule):
    """
    Base class for extractor modules.

    Extractors download content from URLs. They can optionally define a
    valid_url regex pattern for URL matching, sanitize URLs before processing,
    and provide cleanup after extraction completes.

    Attributes:
        valid_url: Optional regex pattern for matching supported URLs
    """

    valid_url: re.Pattern = None

    def cleanup(self) -> None:
        """
        Cleans up resources after extraction.

        Called when extraction is complete or on error. Override to release
        resources like browser instances or temporary files.
        """
        pass

    def sanitize_url(self, url: str) -> str:
        """
        Cleans and transforms a URL before processing.

        Can be used to remove tracking parameters, expand shortened URLs,
        or normalize URL formats. Default implementation returns unchanged.

        Args:
            url: Original URL

        Returns:
            Cleaned URL
        """
        return url

    def match_link(self, url: str) -> re.Match:
        """
        Tests if URL matches this extractor's pattern.

        Args:
            url: URL to test

        Returns:
            Match object if URL matches valid_url pattern, None otherwise
        """
        if self.valid_url:
            return self.valid_url.match(url)
        return None

    def suitable(self, url: str) -> bool:
        """
        Checks if this extractor can handle the given URL.

        Override in subclasses for custom logic. Default implementation
        uses valid_url pattern if defined, otherwise returns True.

        Args:
            url: URL to check

        Returns:
            True if extractor can handle this URL
        """
        if self.valid_url:
            return self.match_link(url) is not None
        return True

    def _guess_file_type(self, path: str) -> str:
        """
        Guesses the general media type from a path or URL.

        Args:
            path: File path or URL

        Returns:
            Media type like 'image', 'video', 'audio', or empty string
        """
        mime = mimetypes.guess_type(path)[0]
        if mime is not None:
            return mime.split("/")[0]
        return ""

    @retry(wait_random_min=500, wait_random_max=3500, stop_max_attempt_number=5)
    def download_from_url(
        self,
        url: str,
        to_filename: str = None,
        verbose: bool = True,
        try_best_quality: bool = False
    ) -> Union[str, tuple, None]:
        """
        Downloads a file from URL to local filesystem.

        Retries on failure with exponential backoff. Can optionally attempt
        to find a higher quality version of the media.

        Args:
            url: URL to download
            to_filename: Target filename (inferred from URL if not provided)
            verbose: Whether to log download progress
            try_best_quality: Whether to try finding higher quality version

        Returns:
            Local filename on success, or tuple (filename, best_url) if
            try_best_quality is True. Returns None on failure.
        """
        if any(url.startswith(x) for x in ["blob:", "data:"]):
            return (None, url) if try_best_quality else None

        if not to_filename:
            to_filename = url.split("/")[-1].split("?")[0]
            if len(to_filename) > 64:
                to_filename = to_filename[-64:]

        if self.tmp_dir:
            to_filename = os.path.join(self.tmp_dir, to_filename)

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/81.0.4044.138 Safari/537.36"
            )
        }

        try:
            response = requests.get(url, stream=True, headers=headers, timeout=30)
            response.raise_for_status()

            if not mimetypes.guess_type(to_filename)[0]:
                content_type = response.headers.get("Content-Type") or self._guess_file_type(url)
                extension = mimetypes.guess_extension(content_type)
                if extension:
                    to_filename += extension

            with open(to_filename, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            return (to_filename, url) if try_best_quality else to_filename

        except requests.RequestException:
            pass

        return (None, url) if try_best_quality else None

    @abstractmethod
    def download(self, item: Metadata) -> Union[Metadata, bool]:
        """
        Downloads content for the given item.

        Implementations should download media from the item's URL and add
        Media objects to the item, then return the item with success status.

        Args:
            item: Metadata object containing URL to download

        Returns:
            Metadata with downloaded content, or False on failure
        """
        pass
