"""Sample database module for testing."""

from webkeeper.core import Database, Metadata


class SampleDatabase(Database):
    """Test database that tracks calls."""

    def __init__(self):
        self.started_items = []
        self.done_items = []
        self.failed_items = []
        self.aborted_items = []

    def started(self, item: Metadata):
        self.started_items.append(item)

    def done(self, item: Metadata, cached: bool = False):
        self.done_items.append((item, cached))

    def failed(self, item: Metadata, reason: str):
        self.failed_items.append((item, reason))

    def aborted(self, item: Metadata):
        self.aborted_items.append(item)
