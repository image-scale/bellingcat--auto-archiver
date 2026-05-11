"""Sample storage module for testing."""

from webkeeper.core import Storage, Media


class SampleStorage(Storage):
    """Test storage that tracks uploads."""

    def __init__(self):
        self.uploads = []

    def get_cdn_url(self, media: Media) -> str:
        return f"http://test-cdn.com/{media.key}"

    def uploadf(self, file, media, **kwargs) -> bool:
        self.uploads.append(media.key)
        return True
