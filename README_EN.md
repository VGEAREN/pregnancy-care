# pregnancy-care

An OpenClaw skill for managing pregnancy health data via chat.

[中文](README.md)

## Features

- **Report Recognition**: Send checkup report photos, AI automatically extracts key indicators and archives structured data
- **Trend Tracking**: Auto-generates trend tables by category (CBC, thyroid, urinalysis, etc.)
- **Ultrasound Management**: Supports both photos and DICOM raw images with automatic measurement extraction
- **Anomaly Analysis**: Cross-references trimester-specific ranges and knowledge base to distinguish normal physiological changes from concerns
- **Checkup Planning**: Maintains a checkup timeline based on gestational age
- **PDF Reports**: One-click comprehensive PDF report with trend tables
- **Knowledge Base**: Extensible book-based reference library with chapter-level citations

## Installation

```bash
# Install from GitHub
openclaw skills install <github-url>

# Or copy manually
cp -r pregnancy-care ~/.openclaw/skills/

# Install Python dependencies (required)
pip3 install reportlab

# Optional: DICOM image support
pip3 install pydicom Pillow numpy

# Optional: add books to knowledge base
pip3 install ebooklib beautifulsoup4
```

## Usage

On first use, the skill guides you through initialization (basic info, data directory creation). Then:

| Action | How |
|--------|-----|
| Log a checkup report | Send report photo(s) |
| Log an ultrasound | Send ultrasound photo or DICOM ZIP |
| Generate PDF report | Send "generate PDF report" |
| Ask pregnancy questions | Ask directly, e.g. "Is elevated TSH normal in first trimester?" |
| Add knowledge base book | Send an epub file |
| View checkup plan | Send "checkup plan" |

## Knowledge Base

The `references/books/` directory is empty by default (copyright). Add your own books:

```bash
python3 scripts/epub-to-md.py "your-book.epub" "references/books/BookName/"
```

Then ask the bot to update the knowledge base index.

## Project Structure

```
pregnancy-care/
├── SKILL.md                  ← Main agent instruction file
├── references/
│   ├── INDEX.md              ← Global topic index across all books
│   ├── indicator-ranges.md   ← Pregnancy indicator reference ranges
│   └── books/                ← Knowledge base books (user adds)
├── scripts/
│   ├── epub-to-md.py         ← Convert epub to per-chapter Markdown
│   ├── dicom-export.py       ← DICOM ZIP to JPG export
│   └── generate-pdf.py       ← Generate comprehensive PDF report
└── assets/                   ← Runtime output
```

## Data Storage

All data is stored as Markdown files in the `pregnancy/` directory within the workspace:

```
pregnancy/
├── profile.md       ← Basic info (name, age, due date)
├── summary.md       ← Indicator trend tables + checkup plan
├── records/         ← Structured reports
├── reports/         ← Original report images
├── ocr_results/     ← OCR raw text
└── ultrasound/      ← Ultrasound images
```

## Disclaimer

All analysis is for reference only and does not constitute medical advice. Consult your doctor for any health concerns.

## License

MIT
