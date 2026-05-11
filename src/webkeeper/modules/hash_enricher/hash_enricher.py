"""Hash enricher module for computing cryptographic hashes of media files."""

import hashlib
from loguru import logger

from webkeeper.core import Enricher, Metadata


def calculate_file_hash(filename: str, hash_algo, chunksize: int) -> str:
    """Calculate hash of a file by reading in chunks."""
    h = hash_algo()
    with open(filename, "rb") as f:
        while True:
            buf = f.read(chunksize)
            if not buf:
                break
            h.update(buf)
    return h.hexdigest()


class HashEnricher(Enricher):
    """Enricher that calculates cryptographic hashes for media files."""

    def enrich(self, item: Metadata) -> None:
        """Calculate hash for each media file and store in metadata."""
        logger.debug(f"Calculating media hashes with algorithm={self.algorithm}")

        for i, media in enumerate(item.media):
            if not media.filename:
                logger.warning(f"Skipping hash for media without filename: {media}")
                continue

            file_hash = self.calculate_hash(media.filename)
            if file_hash:
                item.media[i].set("hash", f"{self.algorithm}:{file_hash}")

    def calculate_hash(self, filename: str) -> str:
        """Calculate hash of a file using configured algorithm."""
        if self.algorithm == "SHA-256":
            hash_algo = hashlib.sha256
        elif self.algorithm == "SHA3-512":
            hash_algo = hashlib.sha3_512
        else:
            return ""

        return calculate_file_hash(filename, hash_algo, self.chunksize)
