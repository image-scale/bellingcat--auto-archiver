"""CLI Feeder module for providing URLs from command line."""

from webkeeper.core import Feeder, Metadata, SetupError


class CLIFeeder(Feeder):
    """Feeder that provides URLs passed via command line arguments."""

    def setup(self) -> None:
        """Validate that URLs were provided."""
        self.urls = self.config.get("urls")
        if not self.urls:
            raise SetupError(
                "No URLs provided. Provide at least one URL via command line, "
                "or configure an alternative feeder. Use --help for more information."
            )

    def __iter__(self):
        """Yield Metadata objects for each URL."""
        for url in self.urls:
            yield Metadata().set_url(url)
