"""Sample feeder module for testing."""

from webkeeper.core import Feeder, Metadata


class SampleFeeder(Feeder):
    """Test feeder that yields configured URLs."""

    def setup(self):
        self.urls = getattr(self, 'urls', ['https://example.com'])
        self.setup_called = True

    def __iter__(self):
        for url in self.urls:
            yield Metadata().set_url(url)
