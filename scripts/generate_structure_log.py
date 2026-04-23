#!/usr/bin/env python3
"""
📚 Generate Library Structure Log — AI-Optimized Format

Quét data.json (source of truth) để tạo file library_structure.log
dạng text thuần, dễ đọc cho AI Agent trước khi phân loại sách.

Output format:
- Liệt kê tất cả categories, topics, subtopics
- Đếm số sách trong mỗi folder
- Liệt kê tên file sách cụ thể (giúp AI tránh trùng lặp)

Usage:
    python scripts/generate_structure_log.py --base-dir .
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path


CATEGORY_PATTERN = re.compile(r'^(\d+)_(.+)$')


def parse_file_path(file_path: str) -> dict:
    """Parse a book's file_path into category, topic, subtopic, filename.

    Args:
        file_path: e.g. 'Books/2_Software_Engineering_Disciplines/DevOps/file.pdf'

    Returns:
        Dict with keys: category, topic, subtopic (optional), filename
    """
    parts = Path(file_path).parts
    # Expected: ('Books', 'N_Category', 'Topic', [Subtopic,] 'file.ext')
    if len(parts) < 4:
        return None

    result = {
        'category': parts[1],
        'topic': parts[2],
        'subtopic': None,
        'filename': parts[-1],
    }
    if len(parts) == 5:
        result['subtopic'] = parts[3]
        # filename is already parts[-1]
    elif len(parts) > 5:
        # Deep nesting — join middle parts as subtopic
        result['subtopic'] = '/'.join(parts[3:-1])

    return result


def generate_log(base_dir: str) -> str:
    """Generate the library structure log from data.json.

    Args:
        base_dir: Root directory of the project.

    Returns:
        Formatted string for library_structure.log
    """
    data_path = Path(base_dir) / 'site' / 'data.json'
    if not data_path.exists():
        return "ERROR: site/data.json not found."

    with open(data_path, 'r', encoding='utf-8') as f:
        books = json.load(f)

    # Build tree structure:
    # categories -> topics -> subtopics -> [filenames]
    tree = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    category_order = {}  # category_folder -> number prefix for sorting

    for book in books:
        fp = book.get('file_path', '')
        parsed = parse_file_path(fp)
        if not parsed:
            continue

        cat = parsed['category']
        topic = parsed['topic']
        subtopic = parsed['subtopic'] or '__root__'
        filename = parsed['filename']

        tree[cat][topic][subtopic].append(filename)

        # Extract sort order from category prefix
        match = CATEGORY_PATTERN.match(cat)
        if match:
            category_order[cat] = int(match.group(1))

    # Sort categories by numeric prefix
    sorted_cats = sorted(tree.keys(), key=lambda c: category_order.get(c, 999))

    # Build output
    lines = []
    lines.append("=" * 60)
    lines.append("LIBRARY STRUCTURE LOG")
    lines.append(f"Generated from: site/data.json ({len(books)} books total)")
    lines.append("=" * 60)
    lines.append("")

    for cat in sorted_cats:
        match = CATEGORY_PATTERN.match(cat)
        if match:
            cat_readable = match.group(2).replace('_', ' ')
            cat_num = match.group(1)
        else:
            cat_readable = cat
            cat_num = '?'

        # Count total books in category
        cat_book_count = sum(
            len(files)
            for topics in tree[cat].values()
            for files in topics.values()
        )

        lines.append(f"[{cat_num}] {cat} ({cat_book_count} books)")
        lines.append(f"    Display Name: {cat_readable}")

        sorted_topics = sorted(tree[cat].keys())
        for t_idx, topic in enumerate(sorted_topics):
            is_last_topic = (t_idx == len(sorted_topics) - 1)
            branch = "└──" if is_last_topic else "├──"

            # Count books in this topic (including subtopics)
            topic_book_count = sum(len(files) for files in tree[cat][topic].values())

            lines.append(f"    {branch} {topic} ({topic_book_count} books)")

            subtopics = tree[cat][topic]
            # Check if there are real subtopics (not just __root__)
            real_subtopics = [s for s in subtopics if s != '__root__']
            root_files = subtopics.get('__root__', [])

            # List root-level files in this topic
            prefix = "    │   " if not is_last_topic else "        "
            if root_files:
                for f_idx, fname in enumerate(sorted(root_files)):
                    lines.append(f"{prefix}    • {fname}")

            # List subtopics
            for s_idx, sub in enumerate(sorted(real_subtopics)):
                is_last_sub = (s_idx == len(real_subtopics) - 1)
                sub_branch = "└──" if is_last_sub else "├──"
                sub_files = subtopics[sub]

                lines.append(f"{prefix}{sub_branch} {sub} ({len(sub_files)} books)")
                for fname in sorted(sub_files):
                    lines.append(f"{prefix}        • {fname}")

        lines.append("")

    lines.append("=" * 60)
    lines.append("AVAILABLE CATEGORIES (for classification):")
    lines.append("")
    for cat in sorted_cats:
        match = CATEGORY_PATTERN.match(cat)
        if match:
            lines.append(f"  {cat}")
            # List all topics
            for topic in sorted(tree[cat].keys()):
                subtopics = [s for s in tree[cat][topic] if s != '__root__']
                if subtopics:
                    for sub in sorted(subtopics):
                        lines.append(f"    -> {topic}/{sub}")
                else:
                    lines.append(f"    -> {topic}")
    lines.append("")
    next_num = max(category_order.values(), default=0) + 1
    lines.append(f"Next available category number: {next_num}")
    lines.append("=" * 60)

    return '\n'.join(lines)


def main():
    """Entry point for generate_structure_log.py."""
    parser = argparse.ArgumentParser(
        description='Generate library_structure.log from data.json'
    )
    parser.add_argument(
        '--base-dir', default='.',
        help='Base directory of the library (default: current directory)'
    )
    parser.add_argument(
        '--output', default=None,
        help='Output file path (default: library_structure.log in base-dir)'
    )
    args = parser.parse_args()

    log_content = generate_log(args.base_dir)

    output_path = args.output or str(Path(args.base_dir) / 'library_structure.log')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(log_content)

    # Use sys.stdout with utf-8 to avoid Windows cp1252 encoding errors
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    print(f"Generated: {output_path}")
    # Also print to stdout for quick inspection
    print(log_content)


if __name__ == '__main__':
    main()
