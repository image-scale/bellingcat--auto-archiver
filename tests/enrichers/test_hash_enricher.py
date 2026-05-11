"""Tests for the Hash Enricher module."""

import pytest

from webkeeper.core import Metadata, Media
from webkeeper.modules.hash_enricher.hash_enricher import HashEnricher


@pytest.fixture
def hash_enricher():
    """Create a HashEnricher instance with custom config."""
    def _create(algorithm="SHA-256", chunksize=16000000):
        enricher = HashEnricher()
        enricher.config = {"algorithm": algorithm, "chunksize": chunksize}
        enricher.name = "hash_enricher"
        enricher.algorithm = algorithm
        enricher.chunksize = chunksize
        return enricher
    return _create


class TestHashCalculation:
    """Test hash calculation functionality."""

    @pytest.mark.parametrize("algorithm,filename,expected_hash", [
        ("SHA-256", "tests/data/testfile_1.txt",
         "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"),
        ("SHA-256", "tests/data/testfile_2.txt",
         "532eaabd9574880dbf76b9b8cc00832c20a6ec113d682299550d7a6e0f345e25"),
        ("SHA3-512", "tests/data/testfile_1.txt",
         "9ece086e9bac491fac5c1d1046ca11d737b92a2b2ebd93f005d7b710110c0a678288166e7fbe796883a4f2e9b3ca9f484f521d0ce464345cc1aec96779149c14"),
        ("SHA3-512", "tests/data/testfile_2.txt",
         "301bb421c971fbb7ed01dcc3a9976ce53df034022ba982b97d0f27d48c4f03883aabf7c6bc778aa7c383062f6823045a6d41b8a720afbb8a9607690f89fbe1a7"),
    ])
    def test_calculate_hash(self, hash_enricher, algorithm, filename, expected_hash):
        """calculate_hash returns correct hash for file."""
        enricher = hash_enricher(algorithm=algorithm, chunksize=100)
        result = enricher.calculate_hash(filename)
        assert result == expected_hash

    def test_unsupported_algorithm_returns_empty(self, hash_enricher):
        """Unsupported algorithm returns empty string."""
        enricher = hash_enricher(algorithm="MD5")
        result = enricher.calculate_hash("tests/data/testfile_1.txt")
        assert result == ""


class TestEnrichMethod:
    """Test the enrich method."""

    def test_enrich_adds_hash_to_media(self, hash_enricher):
        """enrich adds hash to each media file."""
        enricher = hash_enricher(algorithm="SHA-256", chunksize=100)

        item = Metadata().set_url("https://example.com")
        item.add_media(Media("tests/data/testfile_1.txt"))
        item.add_media(Media("tests/data/testfile_2.txt"))

        enricher.enrich(item)

        assert "SHA-256:" in item.media[0].get("hash")
        assert "SHA-256:" in item.media[1].get("hash")

    def test_enrich_with_no_media_is_noop(self, hash_enricher):
        """enrich does nothing when metadata has no media."""
        enricher = hash_enricher()

        item = Metadata().set_url("https://example.com")
        enricher.enrich(item)

        assert len(item.media) == 0

    def test_enrich_skips_media_without_filename(self, hash_enricher):
        """enrich skips media that has no filename."""
        enricher = hash_enricher()

        item = Metadata().set_url("https://example.com")
        media = Media(filename=None)
        item.add_media(media)

        enricher.enrich(item)

        assert item.media[0].get("hash") is None


class TestDefaultConfig:
    """Test default configuration values."""

    def test_default_algorithm(self, hash_enricher):
        """Default algorithm is SHA-256."""
        enricher = hash_enricher()
        assert enricher.algorithm == "SHA-256"

    def test_default_chunksize(self, hash_enricher):
        """Default chunksize is 16MB."""
        enricher = hash_enricher()
        assert enricher.chunksize == 16000000
