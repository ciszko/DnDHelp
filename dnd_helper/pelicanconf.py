from pathlib import Path

BASE_DIR = Path(__file__).parent

AUTHOR = "Marcin"
SITENAME = "DnDHelp"
SITEURL = ""

PATH = "content"

TIMEZONE = "Europe/Warsaw"

DEFAULT_LANG = "Polish"

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

PLUGINS = ["dnd_parser.dnd_parser"]
THEME = BASE_DIR / "themes" / "DnD"

STATIC_PATHS = ["images", "extra"]

EXTRA_PATH_METADATA = {
    "extra/favicon.ico": {"path": "favicon.ico"},
}

# Blogroll
LINKS = (
    ("Pelican", "https://getpelican.com/"),
    ("Python.org", "https://www.python.org/"),
    ("Jinja2", "https://palletsprojects.com/p/jinja/"),
    ("You can modify those links in your config file", "#"),
)

# Social widget
SOCIAL = (
    ("You can add links in your config file", "#"),
    ("Another social link", "#"),
)

DEFAULT_PAGINATION = 10

# Uncomment following line if you want document-relative URLs when developing
# RELATIVE_URLS = True
