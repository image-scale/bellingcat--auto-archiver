"""
Metadata represents a container for archived item data and associated media files.

The Metadata class stores information about an archived URL including its status,
arbitrary metadata fields, and a list of associated Media objects. It supports
merging metadata from multiple sources, deduplication of media by hash, and
provides convenience methods for common operations like setting timestamps and URLs.
"""

from __future__ import annotations
import hashlib
import os
import datetime
from typing import Any, Dict, List, Union
from dataclasses import dataclass, field
from urllib.parse import urlparse
from dataclasses_json import dataclass_json
from dateutil.parser import parse as parse_dt

from .media import Media


@dataclass_json
@dataclass
class Metadata:
    """
    Container for metadata and media objects associated with an archived item.

    Attributes:
        status: Current status of the archiving process
        metadata: Dictionary of arbitrary metadata fields
        media: List of associated Media objects
    """

    status: str = "no archiver"
    metadata: Dict[str, Any] = field(default_factory=dict)
    media: List[Media] = field(default_factory=list)

    def __post_init__(self):
        """Initialize processing timestamp and context storage."""
        self.set("_processed_at", datetime.datetime.now(datetime.timezone.utc))
        self._context = {}

    def set(self, key: str, val: Any) -> "Metadata":
        """
        Sets a metadata field.

        Args:
            key: Field name
            val: Field value

        Returns:
            self for method chaining
        """
        self.metadata[key] = val
        return self

    def get(self, key: str, default: Any = None, create_if_missing: bool = False) -> Any:
        """
        Gets a metadata field.

        Args:
            key: Field name
            default: Value to return if field not found
            create_if_missing: If True, creates the field with default value

        Returns:
            Field value or default
        """
        if create_if_missing and key not in self.metadata:
            self.metadata[key] = default
        return self.metadata.get(key, default)

    def set_url(self, url: str) -> "Metadata":
        """
        Sets the URL being archived.

        Args:
            url: URL string to archive

        Returns:
            self for method chaining

        Raises:
            AssertionError: If url is empty or not a string
        """
        assert isinstance(url, str) and len(url) > 0, "invalid URL"
        return self.set("url", url)

    def get_url(self) -> str:
        """
        Gets the URL being archived.

        Returns:
            URL string

        Raises:
            AssertionError: If url is not set or invalid
        """
        url = self.get("url")
        assert isinstance(url, str) and len(url) > 0, "invalid URL"
        return url

    @property
    def netloc(self) -> str:
        """Returns the network location (domain) portion of the URL."""
        return urlparse(self.get_url()).netloc

    def success(self, context: str = None) -> "Metadata":
        """
        Marks the archiving as successful.

        Args:
            context: Optional context string to include in status

        Returns:
            self for method chaining
        """
        if context:
            self.status = f"{context}: success"
        else:
            self.status = "success"
        return self

    def is_success(self) -> bool:
        """Returns True if archiving was successful."""
        return "success" in self.status

    def is_empty(self) -> bool:
        """
        Checks if metadata contains any meaningful content.

        Returns True if not successful, has no media, and only contains
        system-generated metadata fields.
        """
        system_fields = {
            "_processed_at", "url", "original_url", "total_bytes",
            "total_size", "archive_duration_seconds"
        }
        meaningful_keys = set(self.metadata.keys()) - system_fields
        return not self.is_success() and len(self.media) == 0 and len(meaningful_keys) == 0

    def set_title(self, title: str) -> "Metadata":
        """Sets the title metadata field."""
        return self.set("title", title)

    def get_title(self) -> str:
        """Gets the title metadata field."""
        return self.get("title")

    def set_content(self, content: str) -> "Metadata":
        """
        Appends content to the content metadata field.

        Args:
            content: Text content to append

        Returns:
            self for method chaining
        """
        existing = self.get("content", "")
        appended = (existing + content + "\n").strip()
        return self.set("content", appended)

    def set_timestamp(self, timestamp: Union[datetime.datetime, str]) -> "Metadata":
        """
        Sets the timestamp metadata field.

        Args:
            timestamp: datetime object or parseable string

        Returns:
            self for method chaining

        Raises:
            AssertionError: If timestamp is not a datetime after parsing
        """
        if isinstance(timestamp, str):
            timestamp = parse_dt(timestamp)
        assert isinstance(timestamp, datetime.datetime), "set_timestamp expects a datetime instance"
        return self.set("timestamp", timestamp)

    def get_timestamp(self, utc: bool = True, iso: bool = True) -> Union[datetime.datetime, str, None]:
        """
        Gets the timestamp metadata field with optional formatting.

        Args:
            utc: If True, converts to UTC timezone
            iso: If True, returns ISO format string

        Returns:
            Timestamp as datetime, ISO string, or None if not set
        """
        ts = self.get("timestamp")
        if not ts:
            return None
        try:
            if isinstance(ts, str):
                ts = datetime.datetime.fromisoformat(ts)
            elif isinstance(ts, float):
                ts = datetime.datetime.fromtimestamp(ts)
            if utc:
                ts = ts.replace(tzinfo=datetime.timezone.utc)
            return ts.isoformat() if iso else ts
        except Exception:
            return None

    def add_media(self, media: Media, id: str = None) -> Media:
        """
        Adds a media object to this metadata.

        Args:
            media: Media object to add
            id: Optional unique identifier for the media

        Returns:
            The added media object

        Raises:
            AssertionError: If id is already used by another media
        """
        if media is None:
            return None
        if id is not None:
            existing = [m for m in self.media if m.get("id") == id]
            assert len(existing) == 0, f"cannot add 2 pieces of media with the same id {id}"
            media.set("id", id)
        self.media.append(media)
        return media

    def get_media_by_id(self, id: str, default=None) -> Media:
        """
        Gets a media object by its id.

        Args:
            id: Media identifier
            default: Value to return if not found

        Returns:
            Media object or default
        """
        for m in self.media:
            if m.get("id") == id:
                return m
        return default

    def get_first_image(self, default=None) -> Media:
        """Returns the first image media or default."""
        for m in self.media:
            if "image" in m.mimetype:
                return m
        return default

    def get_all_media(self) -> List[Media]:
        """Returns a flat list of all media including nested inner media."""
        return [inner for m in self.media for inner in m.all_inner_media(include_self=True)]

    def set_final_media(self, final: Media) -> "Metadata":
        """Sets the final formatted media (e.g., HTML report)."""
        self.add_media(final, "_final_media")
        return self

    def get_final_media(self) -> Media:
        """Gets the final formatted media, falling back to first media."""
        default = self.media[0] if len(self.media) else None
        return self.get_media_by_id("_final_media", default)

    def remove_duplicate_media_by_hash(self) -> None:
        """
        Removes duplicate media based on hash property.

        Media without filenames are kept. Media with missing files are skipped.
        Hash is computed if not already set.
        """
        seen_hashes = set()
        unique_media = []

        for m in self.media:
            if not m.filename:
                unique_media.append(m)
                continue

            h = m.get("hash")
            if not h:
                if not os.path.exists(m.filename):
                    continue
                h = self._compute_hash(m.filename)

            if h and h in seen_hashes:
                continue

            if h:
                seen_hashes.add(h)
            unique_media.append(m)

        self.media = unique_media

    def _compute_hash(self, filename: str, chunksize: int = 16_000_000) -> str:
        """Computes SHA-256 hash of a file in chunks."""
        sha = hashlib.sha256()
        with open(filename, "rb") as f:
            while True:
                chunk = f.read(chunksize)
                if not chunk:
                    break
                sha.update(chunk)
        return sha.hexdigest()

    def set_context(self, key: str, val: Any) -> "Metadata":
        """
        Sets a context value (not serialized, not merged).

        Context is separate from metadata and used for transient state.

        Args:
            key: Context key
            val: Context value

        Returns:
            self for method chaining
        """
        self._context[key] = val
        return self

    def get_context(self, key: str, default: Any = None) -> Any:
        """Gets a context value."""
        return self._context.get(key, default)

    def merge(self, right: "Metadata", overwrite_left: bool = True) -> "Metadata":
        """
        Merges another Metadata instance into this one.

        Args:
            right: Metadata to merge from
            overwrite_left: If True, right's values overwrite this one's

        Returns:
            self for method chaining
        """
        if not right:
            return self

        if not overwrite_left:
            return right.merge(self)

        if right.status and len(right.status):
            self.status = right.status

        if hasattr(right, '_context'):
            self._context.update(right._context)

        for k, v in right.metadata.items():
            if k not in self.metadata or not isinstance(v, (dict, list, set)):
                self.set(k, v)
            else:
                existing = self.get(k)
                if isinstance(v, dict) and isinstance(existing, dict):
                    self.set(k, existing | v)
                elif isinstance(v, set) and isinstance(existing, set):
                    self.set(k, existing | v)
                elif isinstance(v, list) and isinstance(existing, list):
                    self.set(k, existing + v)
                else:
                    self.set(k, v)

        self.media.extend(right.media)
        return self

    def store(self, storages: List[Any] = None) -> None:
        """
        Stores all media to the provided storages.

        Args:
            storages: List of storage backends
        """
        if storages is None:
            storages = []

        self.remove_duplicate_media_by_hash()
        for media in self.media:
            media.store(url=self.get_url(), metadata=self, storages=storages)

    @staticmethod
    def choose_most_complete(results: List["Metadata"]) -> "Metadata":
        """
        Selects the most complete metadata from a list.

        Prioritizes metadata with more media, then more metadata fields.

        Args:
            results: List of Metadata objects to compare

        Returns:
            Most complete Metadata or None if list is empty
        """
        if not results:
            return None
        if len(results) == 1:
            return results[0]

        most_complete = results[0]
        for r in results[1:]:
            if len(r.media) > len(most_complete.media):
                most_complete = r
            elif len(r.media) == len(most_complete.media) and len(r.metadata) > len(most_complete.metadata):
                most_complete = r
        return most_complete

    def __str__(self) -> str:
        return self.__repr__()
