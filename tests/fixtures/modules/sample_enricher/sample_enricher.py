"""Sample enricher module for testing."""

from webkeeper.core import Enricher, Metadata


class SampleEnricher(Enricher):
    """Test enricher that adds a marker to metadata."""

    def enrich(self, to_enrich: Metadata):
        to_enrich.set("enriched", True)
