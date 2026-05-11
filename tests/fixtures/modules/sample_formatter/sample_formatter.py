"""Sample formatter module for testing."""

from webkeeper.core import Formatter, Metadata, Media
import os


class SampleFormatter(Formatter):
    """Test formatter that creates a report file."""

    def format(self, item: Metadata) -> Media:
        if self.tmp_dir:
            filename = os.path.join(self.tmp_dir, "report.html")
            with open(filename, "w") as f:
                f.write(f"<html><body>Report for {item.get_url()}</body></html>")
            return Media(filename=filename)
        return None
