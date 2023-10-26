import re
import yaml
from pelican import signals
from pelican.readers import BaseReader
from pelican.utils import pelican_open

HEADER_RE = re.compile(
    r"\s*^---$"  # File starts with a line of "---" (preceeding blank lines accepted)
    r"(?P<metadata>.+?)"
    r"^(?:---|\.\.\.)$"  # metadata section ends with a line of "---" or "..."
    r"(?P<content>.*)",
    re.MULTILINE | re.DOTALL,
)


# Create a new reader class, inheriting from the pelican.reader.BaseReader
class DnDReader(BaseReader):
    enabled = True
    file_extensions = ["md"]

    def read(self, filename):
        with pelican_open(filename) as text:
            m = HEADER_RE.fullmatch(text)

        if not m:
            return super().read(filename)

        metadata = self.parse_yaml(m["metadata"], filename)

        if not (content := m["content"]):
            content = metadata["opis"]

        return content, metadata

    def parse_yaml(self, metadata, filename):
        meta = yaml.safe_load(metadata)
        meta["title"] = meta["nazwa"]
        if "spells" in filename:
            meta["template"] = "spell"
        elif "items" in filename:
            meta["cat"] = "item"
        return meta


def add_reader(readers):
    readers.reader_classes["md"] = DnDReader


# This is how pelican works.
def register():
    signals.readers_init.connect(add_reader)
