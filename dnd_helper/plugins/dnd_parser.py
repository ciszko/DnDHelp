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
                    f"krąg {meta['krąg']}",
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
        base_tags_by_name = {}

        for article in articles:
            for tag in article.tags:
                if getattr(tag, "type", None) != "class":
                    continue

                splitted = tag.display_name.split(" ", 1)
                base_name = splitted[0]

                if len(splitted) == 1:
                    # base class
                    tag.base_class = base_name
                    if base_name not in base_tags_by_name:
                        base_tags_by_name[base_name] = tag
                        tag.subclasses = []
                        if tag not in tags:
                            tags[tag] = []
                else:
                    # subclass
                    tag.base_class = base_name
                    tag.sub_class = splitted[1]

                    if base_name not in base_tags_by_name:
                        # Create a virtual base tag if it doesn't exist
                        base_tag = type(tag)(
                            f"czar {base_name}",
                            tag.settings,
                            display_name=base_name,
                            type="class",
                        )
                        base_tag.base_class = base_name
                        base_tag.subclasses = []
                        base_tags_by_name[base_name] = base_tag
                        tags[base_tag] = []

                    target_base_tag = base_tags_by_name[base_name]
                    if tag not in target_base_tag.subclasses:
                        target_base_tag.subclasses.append(tag)
                    if tag not in tags[target_base_tag]:
                        tags[target_base_tag].append(tag)

        for base_tag, sub_classes in tags.items():
            tags[base_tag] = sorted(sub_classes, key=lambda t: t.display_name)
            base_tag.subclasses = sorted(
                base_tag.subclasses, key=lambda t: t.display_name
            )

        return dict(sorted(tags.items(), key=lambda x: x[0].display_name))

    class AddContextGenerator(Generator):
        def generate_context(self, *args, **kwargs):
            self.context[spell_class_tags.__name__] = spell_class_tags

            # Ensure all base class tags exist in context['tags'] and have subclasses
            all_articles = self.context.get("articles", [])
            class_tags_dict = spell_class_tags(all_articles)

            # context['tags'] is a list of (tag, articles)
            existing_tags_dict = {t.name: t for t, _ in self.context.get("tags", [])}

            for base_tag in class_tags_dict.keys():
                if base_tag.name in existing_tags_dict:
                    # Update existing tag with subclasses info
                    existing_tag = existing_tags_dict[base_tag.name]
                    existing_tag.subclasses = getattr(base_tag, "subclasses", [])
                else:
                    # Add new virtual tag
                    self.context["tags"].append((base_tag, []))

    class ClassTagGenerator(Generator):
        def generate_output(self, writer):
            all_articles = self.context.get("articles", [])
            class_tags_dict = spell_class_tags(all_articles)

            # Pelican's TagsGenerator might skip tags with no articles.
            # We force generation for base class tags.
            for base_tag in class_tags_dict.keys():
                # Check if it was already written (has articles)
                has_articles = False
                for t, articles in self.context.get("tags", []):
                    if t.name == base_tag.name and articles:
                        has_articles = True
                        break

                if not has_articles:
                    template = self.get_template("tag")
                    writer.write_file(
                        base_tag.save_as,
                        template,
                        self.context,
                        tag=base_tag,
                        articles=[],
                        template_name="tag",
                    )

    return [AddContextGenerator, ClassTagGenerator]


def register():
    signals.get_generators.connect(get_generators)
    signals.readers_init.connect(add_reader)
