"""
Media represents a single media file with its metadata and storage information.

The Media class holds information about an archived file including its local path,
remote URLs after storage, mimetype detection, and arbitrary properties. It supports
nested media through properties, enabling hierarchical relationships like thumbnails
or extracted frames.
"""

from __future__ import annotations
import os
import mimetypes
from typing import Any, Iterator, List
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config


@dataclass_json
@dataclass
class Media:
    """
    Represents a media file with associated properties and storage details.

    Attributes:
        filename: The local file path of the media.
        _key: Storage key used for identifying the file in storage backends.
        urls: List of URLs where the media is stored or accessible.
        properties: Additional metadata or nested media objects.
        _mimetype: Cached mimetype of the media file.
    """

    filename: str = None
    _key: str = None
    urls: List[str] = field(default_factory=list)
    properties: dict = field(default_factory=dict)
    _mimetype: str = None
    _stored: bool = field(default=False, repr=False, metadata=config(exclude=lambda _: True))

    @property
    def key(self) -> str:
        """Returns the storage key for this media."""
        return self._key

    @property
    def mimetype(self) -> str:
        """
        Returns the MIME type of the media file.

        Lazily detects the mimetype from the filename if not already set.
        Returns empty string if filename is empty or mimetype cannot be determined.
        """
        if not self.filename or len(self.filename) == 0:
            return ""
        if not self._mimetype:
            guessed = mimetypes.guess_type(self.filename)[0]
            self._mimetype = guessed
        return self._mimetype or ""

    @mimetype.setter
    def mimetype(self, value: str) -> None:
        """Sets the MIME type explicitly."""
        self._mimetype = value

    def is_video(self) -> bool:
        """Returns True if this media is a video file."""
        return self.mimetype.startswith("video")

    def is_audio(self) -> bool:
        """Returns True if this media is an audio file."""
        return self.mimetype.startswith("audio")

    def is_image(self) -> bool:
        """Returns True if this media is an image file."""
        return self.mimetype.startswith("image")

    def set(self, key: str, value: Any) -> "Media":
        """
        Sets a property on this media.

        Args:
            key: Property name
            value: Property value (can be another Media for nested relationships)

        Returns:
            self for method chaining
        """
        self.properties[key] = value
        return self

    def get(self, key: str, default: Any = None) -> Any:
        """
        Gets a property from this media.

        Args:
            key: Property name
            default: Value to return if property not found

        Returns:
            Property value or default
        """
        return self.properties.get(key, default)

    def add_url(self, url: str) -> None:
        """Adds a storage URL to this media's URL list."""
        self.urls.append(url)

    def all_inner_media(self, include_self: bool = False) -> Iterator["Media"]:
        """
        Yields all nested media objects within this media's properties.

        Recursively traverses properties to find Media objects, supporting
        both direct Media values and lists of Media objects.

        Args:
            include_self: If True, yields this media first before nested media

        Yields:
            Media objects found in properties
        """
        if include_self:
            yield self

        for prop_value in self.properties.values():
            if isinstance(prop_value, Media):
                yield from prop_value.all_inner_media(include_self=True)
            elif isinstance(prop_value, list):
                for item in prop_value:
                    if isinstance(item, Media):
                        yield from item.all_inner_media(include_self=True)

    def is_stored(self, in_storage) -> bool:
        """
        Checks if the media has been stored in all configured storages.

        Args:
            in_storage: Storage instance with config containing steps.storages

        Returns:
            True if URLs count matches storage count, False otherwise
        """
        storage_count = len(in_storage.config.get("steps", {}).get("storages", []))
        return len(self.urls) > 0 and len(self.urls) >= storage_count

    def store(self, metadata: Any, url: str = "url-not-available", storages: List[Any] = None) -> None:
        """
        Stores this media and all inner media to the provided storages.

        Args:
            metadata: Metadata object associated with this media
            url: Original URL being archived
            storages: List of storage backends to use
        """
        if storages is None:
            storages = []

        if not storages:
            return

        for storage in storages:
            for media in self.all_inner_media(include_self=True):
                storage.store(media, url, metadata=metadata)

    def is_valid_video(self) -> bool:
        """
        Validates that this video file has actual video content.

        Uses ffmpeg to probe for video streams, falling back to file size check.

        Returns:
            True if video appears valid, False otherwise
        """
        try:
            import ffmpeg
            from ffmpeg._run import Error

            try:
                streams = ffmpeg.probe(self.filename, select_streams="v")["streams"]
                return any(s.get("duration_ts", 0) > 0 for s in streams)
            except Error:
                return False
            except Exception:
                try:
                    fsize = os.path.getsize(self.filename)
                    return fsize > 20_000
                except Exception:
                    pass
        except ImportError:
            pass

        return True
