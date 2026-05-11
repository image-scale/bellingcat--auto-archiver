"""Mute formatter module that produces no output."""

from webkeeper.core import Formatter, Metadata, Media


class MuteFormatter(Formatter):
    """Formatter that produces no output (returns None)."""

    def format(self, item: Metadata) -> Media:
        """Return None - no formatting output."""
        return None
