#!/usr/bin/env python3
"""
Convert epub files to per-chapter Markdown files for the pregnancy-care knowledge base.

Usage:
    python3 epub-to-md.py <input_file> <output_dir>

Example:
    python3 epub-to-md.py "梅奥健康怀孕全书.epub" "references/books/梅奥健康怀孕全书/"

Output:
    output_dir/
    ├── META.md          ← Book metadata + chapter index
    ├── ch01-章节名.md
    ├── ch02-章节名.md
    └── ...

Dependencies:
    pip3 install ebooklib beautifulsoup4
"""

import sys
import os
import re
from pathlib import Path


def check_dependencies():
    """Check and report missing dependencies."""
    missing = []
    try:
        import ebooklib
    except ImportError:
        missing.append("ebooklib")
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        missing.append("beautifulsoup4")
    if missing:
        print(f"Error: Missing dependencies: {', '.join(missing)}")
        print(f"Install with: pip3 install {' '.join(missing)}")
        sys.exit(1)


def html_to_markdown(html_content):
    """Convert HTML content to clean Markdown text."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html_content, "html.parser")

    for tag in soup.find_all(["script", "style", "img"]):
        tag.decompose()

    for level in range(1, 7):
        for heading in soup.find_all(f"h{level}"):
            text = heading.get_text(strip=True)
            if text:
                heading.replace_with(f"\n{'#' * level} {text}\n\n")

    for tag in soup.find_all(["strong", "b"]):
        text = tag.get_text(strip=True)
        if text:
            tag.replace_with(f"**{text}**")

    for tag in soup.find_all(["em", "i"]):
        text = tag.get_text(strip=True)
        if text:
            tag.replace_with(f"*{text}*")

    for ul in soup.find_all("ul"):
        items = []
        for li in ul.find_all("li", recursive=False):
            text = li.get_text(strip=True)
            if text:
                items.append(f"- {text}")
        if items:
            ul.replace_with("\n" + "\n".join(items) + "\n")

    for ol in soup.find_all("ol"):
        items = []
        for idx, li in enumerate(ol.find_all("li", recursive=False), 1):
            text = li.get_text(strip=True)
            if text:
                items.append(f"{idx}. {text}")
        if items:
            ol.replace_with("\n" + "\n".join(items) + "\n")

    for p in soup.find_all("p"):
        text = p.get_text(strip=True)
        if text:
            p.replace_with(f"\n{text}\n")

    text = soup.get_text()
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = text.strip()

    return text


def extract_title_from_html(html_content):
    """Try to extract a chapter title from HTML content."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html_content, "html.parser")

    for tag_name in ["h1", "h2", "title"]:
        tag = soup.find(tag_name)
        if tag:
            text = tag.get_text(strip=True)
            if text and len(text) < 100:
                return text

    return None


def sanitize_filename(name):
    """Make a string safe for use as a filename."""
    name = re.sub(r'[<>:"/\\|?*]', "", name)
    name = re.sub(r"\s+", "-", name.strip())
    return name[:80]


def convert_epub(input_path, output_dir):
    """Convert an epub file to per-chapter Markdown files."""
    import ebooklib
    from ebooklib import epub

    print(f"Reading: {input_path}")
    book = epub.read_epub(input_path)

    os.makedirs(output_dir, exist_ok=True)

    title = book.get_metadata("DC", "title")
    title = title[0][0] if title else Path(input_path).stem
    author = book.get_metadata("DC", "creator")
    author = author[0][0] if author else "Unknown"

    chapters = []
    chapter_num = 0

    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        content = item.get_content().decode("utf-8", errors="replace")
        markdown = html_to_markdown(content)

        if len(markdown.strip()) < 50:
            continue

        chapter_num += 1
        chapter_title = extract_title_from_html(content) or f"Chapter {chapter_num}"
        safe_title = sanitize_filename(chapter_title)
        filename = f"ch{chapter_num:02d}-{safe_title}.md"

        chapter_path = os.path.join(output_dir, filename)
        with open(chapter_path, "w", encoding="utf-8") as f:
            f.write(markdown)

        chapters.append(
            {"num": chapter_num, "title": chapter_title, "filename": filename}
        )
        print(f"  [{chapter_num:02d}] {chapter_title} -> {filename}")

    meta_path = os.path.join(output_dir, "META.md")
    with open(meta_path, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n")
        f.write(f"## 信息\n")
        f.write(f"- 作者：{author}\n")
        f.write(f"- 来源格式：epub\n")
        f.write(f"- 章节数：{len(chapters)}\n\n")
        f.write(f"## 章节目录\n")
        for ch in chapters:
            f.write(f"{ch['num']}. [{ch['title']}]({ch['filename']})\n")

    print(f"\nDone! {len(chapters)} chapters -> {output_dir}")
    print(f"META.md created at {meta_path}")
    return chapters


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 epub-to-md.py <input_file> <output_dir>")
        print("  Supported formats: .epub")
        print("  Example: python3 epub-to-md.py book.epub references/books/bookname/")
        sys.exit(1)

    check_dependencies()

    input_path = sys.argv[1]
    output_dir = sys.argv[2]

    if not os.path.exists(input_path):
        print(f"Error: File not found: {input_path}")
        sys.exit(1)

    ext = Path(input_path).suffix.lower()
    if ext == ".epub":
        convert_epub(input_path, output_dir)
    else:
        print(f"Error: Unsupported format '{ext}'. Currently supported: .epub")
        sys.exit(1)


if __name__ == "__main__":
    main()
