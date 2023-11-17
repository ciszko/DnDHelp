from datetime import datetime
import re
import yaml
from pathlib import Path
from pelican import signals
from pelican.readers import BaseReader
from pelican.generators import Generator
from pelican.utils import pelican_open
from pelican.contents import Tag as BaseTag, Article

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


class SpellTag(BaseTag):
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

def get_generators(pelican_object):

    def spell_class_tags(articles: Article):
        """Processes tags, returns list of unique spell class tags"""
        tags = {}
        for article in articles:
            for tag in article.tags:
                if tag.type != "class":
                    continue
                if len(splitted:= tag.display_name.split(" ", 1)) == 1:
                    # base class       
                    tag.base_class = tag.display_name
                    if tag not in tags.keys():
                        tags[tag] = []
                else:
                    # subclass
                    base, sub = splitted
                    tag.base_class = base
                    tag.sub_class = sub
                    for base_tag, sub_tag in tags.items():
                        if base_tag.base_class != tag.base_class:
                            continue
                        if tag in sub_tag:
                            continue
                        sub_tag.append(tag)
        for base_class, sub_classes in tags.items():
            tags[base_class] = sorted(sub_classes, key=lambda t: t.display_name)
        return dict(sorted(tags.items()))

    class AddContextGenerator(Generator):
        def generate_context(self, *args, **kwargs):
            self.context[spell_class_tags.__name__] = spell_class_tags
            
    return AddContextGenerator




def register():
    signals.get_generators.connect(get_generators)
    signals.readers_init.connect(add_reader)
