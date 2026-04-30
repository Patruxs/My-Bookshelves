"""Project-wide constants for My Bookshelves scripts."""

from __future__ import annotations

import re

BOOKS_DIR = "Books"
INBOX_DIR = "Inbox"
DATA_JSON = "site/data.json"
COVER_DIR = "site/assets/covers"
COVER_WEB_PATH = "assets/covers"
BOOK_EXTENSIONS = {".pdf", ".epub", ".docx"}
DEFAULT_RELEASE_TAG = "storage-v1"
COVER_WIDTH = 600
COVER_QUALITY = 85
COVER_FORMAT = "webp"
COVER_SIZE_WARNING_BYTES = 80 * 1024
CATEGORY_PATTERN = re.compile(r"^(\d+)_(.+)$")

