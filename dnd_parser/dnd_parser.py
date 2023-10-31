from datetime import datetime
import re
import yaml
from pathlib import Path
from pelican import signals
from pelican.readers import BaseReader
from pelican.utils import pelican_open
from pelican.contents import Tag as BaseTag

HEADER_RE = re.compile(
    r"\s*^---$"  # File starts with a line of "---" (preceeding blank lines accepted)
    r"(?P<metadata>.+?)"
    r"^(?:---|\.\.\.)$"  # metadata section ends with a line of "---" or "..."
    r"(?P<content>.*)",
    re.MULTILINE | re.DOTALL,
)


class Tag(BaseTag):
    def __init__(self, name, *args, display_name=None, type=None, **kwargs):
        super().__init__(name, *args, **kwargs)
        self.display_name = display_name if display_name else name
        self.type = type


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
            if metadata.get("content", None):
                content = metadata["opis"]

        if metadata.get("date", None) is None:
            metadata["date"] = datetime(2023, 1, 1)

        if metadata.get("title", None) is None:
            metadata["title"] = metadata["nazwa"]

        return content, metadata

    def parse_yaml(self, metadata, filename):
        meta = yaml.safe_load(metadata)
        f = Path(filename)
        if not any(x in f.parts for x in ("czary", "przedmioty")):
            return meta
        meta["title"] = meta["nazwa"]
        if "czary" in filename:
            meta["template"] = "spell"
            meta["tags"] = [
                Tag(
                    f"czar {x}",
                    self.settings,
                    display_name=x,
                    type="class",
                )
                for x in meta["klasa"]
            ]
            meta["tags"].append(
                Tag(
                    f'krąg {meta["krąg"]}',
                    self.settings,
                    display_name=f"Krąg {meta['krąg']}",
                    type="circle",
                )
            )
        elif "przedmioty" in filename:
            meta["template"] = "item"
            meta["tags"] = [Tag(meta["rzadkość"], self.settings, type="rarity")]
        return meta


def add_reader(readers):
    readers.reader_classes["md"] = DnDReader


def register():
    signals.readers_init.connect(add_reader)
