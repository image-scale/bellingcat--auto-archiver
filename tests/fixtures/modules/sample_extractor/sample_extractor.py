"""Sample extractor module for testing."""

from webkeeper.core import Extractor, Metadata, Media
import os


class SampleExtractor(Extractor):
    """Test extractor that creates a simple file."""

    def download(self, item: Metadata) -> Metadata:
        if self.tmp_dir:
            filename = os.path.join(self.tmp_dir, "sample.txt")
            with open(filename, "w") as f:
                f.write(f"Content from {item.get_url()}")
            item.add_media(Media(filename=filename))
        item.success("sample_extractor")
        return item

    def cleanup(self):
        self.cleaned_up = True
