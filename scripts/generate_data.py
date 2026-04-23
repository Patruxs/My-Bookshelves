#!/usr/bin/env python3
"""
📚 My Bookshelves — Data Generator (Agent 2: Python/Data Engineer)

Scans the book directory structure, extracts cover images from PDF/EPUB files,
and generates a data.json file for the frontend.

Usage:
    cd scripts/
    python generate_data.py [--base-dir ..] [--force]
"""

import os
import sys
import json
import re
import argparse
import hashlib
from pathlib import Path

# ── Optional imports (graceful fallback) ──
try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False
    print("⚠️  PyMuPDF not installed. PDF cover extraction disabled.")
    print("   Install with: pip install PyMuPDF")

try:
    from PIL import Image
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False

try:
    import ebooklib
    from ebooklib import epub
    HAS_EBOOKLIB = True
except ImportError:
    HAS_EBOOKLIB = False
    print("⚠️  ebooklib not installed. EPUB cover extraction disabled.")
    print("   Install with: pip install ebooklib")


# ── Configuration ──
BOOK_EXTENSIONS = {'.pdf', '.epub'}
COVER_DIR = 'site/assets/covers'       # Filesystem path (relative to base_dir)
COVER_WEB_PATH = 'assets/covers'       # Web URL path (relative to site/ root)
OUTPUT_FILE = 'site/data.json'
BOOKS_DIR = 'Books'                    # Folder containing category subfolders
COVER_WIDTH = 600       # Max width for cover thumbnails (sharp on High-DPI/Retina)
COVER_QUALITY = 85      # WebP quality (target: <80KB per image)
COVER_FORMAT = 'webp'   # Output format (webp for maximum compression)

# Category folders expected at root level
CATEGORY_PATTERN = re.compile(r'^(\d+)_(.+)$')


def sanitize_filename(name: str) -> str:
    """Create a safe filename from a book title."""
    name = re.sub(r'[^\w\s\-.]', '', name)
    name = re.sub(r'\s+', '_', name.strip())
    return name[:100]  # Limit length


def parse_category_name(folder_name: str) -> str:
    """Convert folder name like '1_Computer_Science_Fundamentals' to readable name."""
    match = CATEGORY_PATTERN.match(folder_name)
    if match:
        return match.group(2).replace('_', ' ')
    return folder_name.replace('_', ' ')


def parse_topic_name(folder_name: str) -> str:
    """Convert folder name like 'Data_Structures_and_Algorithms' to readable name."""
    return folder_name.replace('_', ' ')


def extract_pdf_cover(pdf_path: str, output_path: str) -> bool:
    """Extract first page of PDF as cover image (WebP, optimized)."""
    if not HAS_PYMUPDF:
        return False
    try:
        doc = fitz.open(pdf_path)
        if doc.page_count == 0:
            doc.close()
            return False

        page = doc[0]
        # Render at 3x for quality before downscale (sharp on Retina)
        zoom = 3.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)

        if HAS_PILLOW:
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            # Resize to max COVER_WIDTH
            if img.width > COVER_WIDTH:
                ratio = COVER_WIDTH / img.width
                new_height = int(img.height * ratio)
                img = img.resize((COVER_WIDTH, new_height), Image.LANCZOS)
            img.save(output_path, 'WEBP', quality=COVER_QUALITY, method=6)
        else:
            pix.save(output_path)

        doc.close()
        return True
    except Exception as e:
        print(f"  ❌ Error extracting PDF cover: {e}")
        return False


def extract_epub_cover(epub_path: str, output_path: str) -> bool:
    """Extract cover image from EPUB file (WebP, optimized)."""
    if not HAS_EBOOKLIB:
        return False
    try:
        book = epub.read_epub(epub_path, options={'ignore_ncx': True})

        cover_image = None

        # Method 1: Look for cover in metadata
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_COVER:
                cover_image = item.get_content()
                break

        # Method 2: Look for images with 'cover' in the name
        if not cover_image:
            for item in book.get_items_of_type(ebooklib.ITEM_IMAGE):
                if 'cover' in item.get_name().lower():
                    cover_image = item.get_content()
                    break

        # Method 3: Use first image found
        if not cover_image:
            for item in book.get_items_of_type(ebooklib.ITEM_IMAGE):
                cover_image = item.get_content()
                break

        if cover_image:
            if HAS_PILLOW:
                from io import BytesIO
                img = Image.open(BytesIO(cover_image))
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                if img.width > COVER_WIDTH:
                    ratio = COVER_WIDTH / img.width
                    new_height = int(img.height * ratio)
                    img = img.resize((COVER_WIDTH, new_height), Image.LANCZOS)
                img.save(output_path, 'WEBP', quality=COVER_QUALITY, method=6)
            else:
                with open(output_path, 'wb') as f:
                    f.write(cover_image)
            return True

        return False
    except Exception as e:
        print(f"  ❌ Error extracting EPUB cover: {e}")
        return False


def generate_book_id(file_path: str) -> str:
    """Generate a unique ID from file path."""
    return hashlib.md5(file_path.encode('utf-8')).hexdigest()[:12]


def scan_books(base_dir: str, force_covers: bool = False) -> list:
    """
    Scan the book directory structure and extract metadata + covers.

    Expected structure:
      base_dir/
        1_Category_Name/
          Topic_Name/
            Book Title.pdf
          SubTopic/
            Book Title.epub
    """
    base = Path(base_dir).resolve()
    covers_dir = base / COVER_DIR
    covers_dir.mkdir(parents=True, exist_ok=True)

    books = []
    skipped = 0
    extracted = 0
    failed = 0

    print(f"\n📂 Scanning: {base}")
    print(f"📁 Covers directory: {covers_dir}\n")

    # Books are inside the Books/ subdirectory
    books_root = base / BOOKS_DIR
    if not books_root.exists():
        print(f"⚠️  Books directory not found: {books_root}")
        return books

    # Iterate category folders
    for cat_folder in sorted(books_root.iterdir()):
        if not cat_folder.is_dir():
            continue
        if not CATEGORY_PATTERN.match(cat_folder.name):
            continue

        category_name = parse_category_name(cat_folder.name)
        print(f"📚 Category: {category_name}")

        # Walk through all subdirectories
        for root, dirs, files in os.walk(cat_folder):
            root_path = Path(root)
            # Determine topic from relative path
            rel_to_cat = root_path.relative_to(cat_folder)
            parts = rel_to_cat.parts

            if len(parts) == 0:
                # Files directly in category folder
                topic_name = category_name
            else:
                # First subfolder is the topic
                topic_name = parse_topic_name(parts[0])

            for filename in sorted(files):
                file_path = root_path / filename
                ext = file_path.suffix.lower()

                if ext not in BOOK_EXTENSIONS:
                    continue

                # Extract book title from filename
                title = file_path.stem

                # Relative path for frontend
                rel_path = file_path.relative_to(base).as_posix()

                # Cover filename (.webp for optimization)
                cover_filename = sanitize_filename(title) + '.webp'
                cover_path = covers_dir / cover_filename
                cover_rel = f"{COVER_WEB_PATH}/{cover_filename}"

                # Also check for old .jpg covers
                old_jpg = covers_dir / (sanitize_filename(title) + '.jpg')
                if old_jpg.exists() and not cover_path.exists():
                    old_jpg.unlink()  # Remove stale JPG

                # Extract cover (skip if exists and not forced)
                has_cover = False
                if cover_path.exists() and not force_covers:
                    has_cover = True
                    skipped += 1
                    print(f"  ⏭️  Skip cover (exists): {title}")
                else:
                    print(f"  🖼️  Extracting cover: {title}...", end=' ')
                    if ext == '.pdf':
                        has_cover = extract_pdf_cover(str(file_path), str(cover_path))
                    elif ext == '.epub':
                        has_cover = extract_epub_cover(str(file_path), str(cover_path))

                    if has_cover:
                        extracted += 1
                        print("✅")
                    else:
                        failed += 1
                        print("❌")

                # Build book entry
                book = {
                    'id': generate_book_id(rel_path),
                    'title': title,
                    'category': category_name,
                    'topic': topic_name,
                    'file_path': rel_path,
                    'cover': cover_rel if has_cover else '',
                    'format': ext[1:],  # 'pdf' or 'epub'
                    'description': '',
                }
                books.append(book)

    print(f"\n{'='*50}")
    print(f"📊 Summary:")
    print(f"   Total books found: {len(books)}")
    print(f"   Covers extracted:  {extracted}")
    print(f"   Covers skipped:    {skipped}")
    print(f"   Covers failed:     {failed}")
    print(f"{'='*50}\n")

    return books


def main():
    parser = argparse.ArgumentParser(description='Generate data.json and cover images for My Bookshelves')
    parser.add_argument('--base-dir', default='..', help='Base directory of the book library (default: parent directory)')
    parser.add_argument('--force', action='store_true', help='Force regenerate all cover images')
    parser.add_argument('--output', default=OUTPUT_FILE, help=f'Output JSON file (default: {OUTPUT_FILE})')
    args = parser.parse_args()

    books = scan_books(args.base_dir, force_covers=args.force)

    # Load existing data.json to preserve descriptions and download_url
    output_path = Path(args.base_dir) / args.output
    existing_descriptions = {}
    existing_download_urls = {}
    existing_by_title = {}
    existing_urls_by_title = {}
    if output_path.exists():
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                existing = json.load(f)
                for entry in existing:
                    desc = entry.get('description', '')
                    url = entry.get('download_url', '')
                    if entry.get('file_path'):
                        if desc:
                            existing_descriptions[entry['file_path']] = desc
                        if url:
                            existing_download_urls[entry['file_path']] = url
                    if entry.get('title'):
                        if desc:
                            existing_by_title[entry['title']] = desc
                        if url:
                            existing_urls_by_title[entry['title']] = url
        except (json.JSONDecodeError, KeyError):
            pass

    # Merge: keep existing descriptions and download_urls (match by file_path first, then title)
    final_books = []
    if 'existing' in locals():
        existing_paths = {b.get('file_path', ''): b for b in existing}
        for book in books:
            if book['file_path'] in existing_descriptions:
                book['description'] = existing_descriptions[book['file_path']]
            elif book['title'] in existing_by_title:
                book['description'] = existing_by_title[book['title']]
            if book['file_path'] in existing_download_urls:
                book['download_url'] = existing_download_urls[book['file_path']]
            elif book['title'] in existing_urls_by_title:
                book['download_url'] = existing_urls_by_title[book['title']]
            
            existing_paths[book['file_path']] = book
            
        final_books = list(existing_paths.values())
    else:
        final_books = books

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_books, f, ensure_ascii=False, indent=2)

    print(f"✅ Generated {output_path} with {len(final_books)} books.")


if __name__ == '__main__':
    main()
