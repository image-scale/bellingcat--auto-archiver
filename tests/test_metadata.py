"""Tests for the Metadata class."""

import pytest
from datetime import datetime, timezone

from webkeeper.core.metadata import Metadata
from webkeeper.core.media import Media


class TestMetadataBasics:
    """Test basic Metadata initialization and properties."""

    def test_initial_state(self):
        """Fresh Metadata has correct default status."""
        m = Metadata()
        assert m.status == "no archiver"
        assert m.media == []
        assert isinstance(m.get("_processed_at"), datetime)

    def test_set_and_get(self):
        """Metadata.set and get work correctly."""
        m = Metadata()
        result = m.set("title", "Test")
        assert result is m
        assert m.get("title") == "Test"

    def test_get_default_value(self):
        """Metadata.get returns default for missing keys."""
        m = Metadata()
        assert m.get("missing") is None
        assert m.get("missing", "default") == "default"


class TestMetadataUrl:
    """Test URL handling."""

    def test_set_and_get_url(self):
        """URL can be set and retrieved."""
        m = Metadata()
        m.set_url("https://example.com")
        assert m.get_url() == "https://example.com"

    def test_set_empty_url_raises(self):
        """Setting empty URL raises AssertionError."""
        m = Metadata()
        with pytest.raises(AssertionError):
            m.set_url("")

    def test_netloc_property(self):
        """netloc returns the domain portion of URL."""
        m = Metadata()
        m.set_url("https://example.com/path/to/page")
        assert m.netloc == "example.com"


class TestMetadataStatus:
    """Test status handling."""

    def test_success_without_context(self):
        """success() sets status to 'success'."""
        m = Metadata()
        assert not m.is_success()
        m.success()
        assert m.is_success()
        assert m.status == "success"

    def test_success_with_context(self):
        """success() with context includes context in status."""
        m = Metadata()
        m.success("extractor")
        assert m.is_success()
        assert m.status == "extractor: success"


class TestMetadataIsEmpty:
    """Test is_empty functionality."""

    def test_fresh_metadata_is_empty(self):
        """Fresh Metadata is considered empty."""
        m = Metadata()
        assert m.is_empty()

    def test_metadata_with_system_fields_is_empty(self):
        """Metadata with only system fields is still empty."""
        m = Metadata()
        m.set("url", "https://example.com")
        m.set("total_bytes", 100)
        m.set("archive_duration_seconds", 10)
        assert m.is_empty()

    def test_metadata_with_custom_field_not_empty(self):
        """Metadata with custom field is not empty."""
        m = Metadata()
        m.set("title", "Test Page")
        assert not m.is_empty()

    def test_successful_metadata_not_empty(self):
        """Successful Metadata is not empty."""
        m = Metadata()
        m.success()
        assert not m.is_empty()

    def test_metadata_with_media_not_empty(self):
        """Metadata with media is not empty."""
        m = Metadata()
        m.add_media(Media(filename="test.jpg"))
        assert not m.is_empty()


class TestMetadataTimestamp:
    """Test timestamp handling."""

    def test_set_timestamp_datetime(self):
        """Timestamp can be set from datetime."""
        m = Metadata()
        ts = datetime(2023, 1, 15, 12, 30, tzinfo=timezone.utc)
        m.set_timestamp(ts)
        assert m.get("timestamp") == ts

    def test_set_timestamp_string(self):
        """Timestamp can be set from parseable string."""
        m = Metadata()
        m.set_timestamp("2023-01-15 12:30:00")
        assert isinstance(m.get("timestamp"), datetime)

    def test_get_timestamp_iso(self):
        """get_timestamp returns ISO format string."""
        m = Metadata()
        ts = datetime(2023, 1, 15, 12, 30, tzinfo=timezone.utc)
        m.set_timestamp(ts)
        result = m.get_timestamp(utc=True, iso=True)
        assert isinstance(result, str)
        assert "2023-01-15" in result

    def test_get_timestamp_none_when_not_set(self):
        """get_timestamp returns None when not set."""
        m = Metadata()
        assert m.get_timestamp() is None


class TestMetadataMedia:
    """Test media management."""

    def test_add_media(self):
        """Media can be added to metadata."""
        m = Metadata()
        media = Media(filename="test.jpg")
        result = m.add_media(media)
        assert result is media
        assert len(m.media) == 1
        assert m.media[0] is media

    def test_add_media_with_id(self):
        """Media can be added with an ID."""
        m = Metadata()
        media = Media(filename="test.jpg")
        m.add_media(media, id="main_image")
        assert media.get("id") == "main_image"

    def test_add_duplicate_id_raises(self):
        """Adding media with duplicate ID raises AssertionError."""
        m = Metadata()
        m.add_media(Media(filename="first.jpg"), id="same_id")
        with pytest.raises(AssertionError):
            m.add_media(Media(filename="second.jpg"), id="same_id")

    def test_get_media_by_id(self):
        """get_media_by_id retrieves correct media."""
        m = Metadata()
        media1 = Media(filename="first.jpg")
        media2 = Media(filename="second.jpg")
        m.add_media(media1, id="first")
        m.add_media(media2, id="second")
        assert m.get_media_by_id("first") is media1
        assert m.get_media_by_id("second") is media2
        assert m.get_media_by_id("missing") is None

    def test_get_first_image(self):
        """get_first_image returns first image media."""
        m = Metadata()
        m.add_media(Media(filename="video.mp4"))
        image = Media(filename="image.jpg")
        m.add_media(image)
        assert m.get_first_image() is image

    def test_get_all_media(self):
        """get_all_media returns flat list including nested."""
        m = Metadata()
        parent = Media(filename="parent.mp4")
        child = Media(filename="child.jpg")
        parent.set("thumbnail", child)
        m.add_media(parent)

        all_media = m.get_all_media()
        assert len(all_media) == 2
        assert parent in all_media
        assert child in all_media

    def test_set_and_get_final_media(self):
        """Final media can be set and retrieved."""
        m = Metadata()
        final = Media(filename="report.html")
        m.set_final_media(final)
        assert m.get_final_media() is final


class TestMetadataDeduplication:
    """Test media deduplication."""

    def test_remove_duplicate_media_by_hash(self, tmp_path):
        """Duplicate media are removed based on hash."""
        m = Metadata()

        file1 = tmp_path / "file1.txt"
        file1.write_text("same content")
        file2 = tmp_path / "file2.txt"
        file2.write_text("same content")
        file3 = tmp_path / "file3.txt"
        file3.write_text("different content")

        m.add_media(Media(filename=str(file1)))
        m.add_media(Media(filename=str(file2)))
        m.add_media(Media(filename=str(file3)))

        assert len(m.media) == 3
        m.remove_duplicate_media_by_hash()
        assert len(m.media) == 2

    def test_remove_duplicate_uses_existing_hash(self, tmp_path):
        """Deduplication uses existing hash property."""
        m = Metadata()

        media1 = Media(filename="doesnt_exist1.txt")
        media1.set("hash", "abc123")
        media2 = Media(filename="doesnt_exist2.txt")
        media2.set("hash", "abc123")
        media3 = Media(filename="doesnt_exist3.txt")
        media3.set("hash", "def456")

        m.add_media(media1)
        m.add_media(media2)
        m.add_media(media3)

        m.remove_duplicate_media_by_hash()
        assert len(m.media) == 2

    def test_remove_duplicate_skips_missing_files(self, tmp_path):
        """Missing files are dropped during deduplication."""
        m = Metadata()

        real_file = tmp_path / "exists.txt"
        real_file.write_text("content")

        m.add_media(Media(filename=str(real_file)))
        m.add_media(Media(filename="/nonexistent/path/gone.mp4"))

        assert len(m.media) == 2
        m.remove_duplicate_media_by_hash()
        assert len(m.media) == 1


class TestMetadataContext:
    """Test context storage."""

    def test_set_and_get_context(self):
        """Context values can be set and retrieved."""
        m = Metadata()
        m.set_context("folder", "/tmp/archive")
        assert m.get_context("folder") == "/tmp/archive"

    def test_get_context_default(self):
        """get_context returns default for missing keys."""
        m = Metadata()
        assert m.get_context("missing") is None
        assert m.get_context("missing", "default") == "default"

    def test_context_is_separate_from_metadata(self):
        """Context is stored separately from metadata dict."""
        m = Metadata()
        m.set_context("key", "context_value")
        m.set("key", "metadata_value")
        assert m.get_context("key") == "context_value"
        assert m.get("key") == "metadata_value"


class TestMetadataMerge:
    """Test metadata merging."""

    def test_merge_status(self):
        """Merge overwrites status."""
        left = Metadata()
        left.status = "old status"
        right = Metadata()
        right.status = "new status"

        left.merge(right)
        assert left.status == "new status"

    def test_merge_metadata_fields(self):
        """Merge copies metadata fields."""
        left = Metadata()
        left.set("title", "Original")
        right = Metadata()
        right.set("title", "Updated")
        right.set("author", "New Author")

        left.merge(right)
        assert left.get("title") == "Updated"
        assert left.get("author") == "New Author"

    def test_merge_extends_lists(self):
        """Merge extends list fields."""
        left = Metadata()
        left.set("tags", ["a", "b"])
        right = Metadata()
        right.set("tags", ["c", "d"])

        left.merge(right)
        assert left.get("tags") == ["a", "b", "c", "d"]

    def test_merge_extends_dicts(self):
        """Merge extends dict fields."""
        left = Metadata()
        left.set("stats", {"views": 10})
        right = Metadata()
        right.set("stats", {"likes": 5})

        left.merge(right)
        assert left.get("stats") == {"views": 10, "likes": 5}

    def test_merge_extends_media(self):
        """Merge extends media list."""
        left = Metadata()
        left.add_media(Media(filename="left.jpg"))
        right = Metadata()
        right.add_media(Media(filename="right.jpg"))

        left.merge(right)
        assert len(left.media) == 2

    def test_merge_none_returns_self(self):
        """Merging None returns self unchanged."""
        m = Metadata()
        m.set("key", "value")
        result = m.merge(None)
        assert result is m
        assert m.get("key") == "value"


class TestMetadataChooseMostComplete:
    """Test choosing most complete metadata."""

    def test_choose_from_empty_list(self):
        """Empty list returns None."""
        assert Metadata.choose_most_complete([]) is None

    def test_choose_from_single(self):
        """Single item returns that item."""
        m = Metadata()
        assert Metadata.choose_most_complete([m]) is m

    def test_choose_by_media_count(self):
        """Item with more media is chosen."""
        m_less = Metadata()
        m_more = Metadata()
        m_more.add_media(Media(filename="1.jpg"))
        m_more.add_media(Media(filename="2.jpg"))

        result = Metadata.choose_most_complete([m_less, m_more])
        assert result is m_more

    def test_choose_by_metadata_count(self):
        """With equal media, item with more metadata is chosen."""
        m_less = Metadata()
        m_less.set("title", "Title")

        m_more = Metadata()
        m_more.set("title", "Title")
        m_more.set("author", "Author")
        m_more.set("description", "Description")

        result = Metadata.choose_most_complete([m_less, m_more])
        assert result is m_more


class TestMetadataContent:
    """Test content handling."""

    def test_set_content(self):
        """Content can be set."""
        m = Metadata()
        m.set_content("Some content")
        assert m.get("content") == "Some content"

    def test_set_content_appends(self):
        """Setting content appends to existing."""
        m = Metadata()
        m.set_content("First")
        m.set_content("Second")
        content = m.get("content")
        assert "First" in content
        assert "Second" in content


class TestMetadataTitle:
    """Test title handling."""

    def test_set_and_get_title(self):
        """Title can be set and retrieved."""
        m = Metadata()
        m.set_title("Test Title")
        assert m.get_title() == "Test Title"
