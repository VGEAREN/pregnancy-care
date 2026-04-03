# pregnancy-care

An OpenClaw skill for managing pregnancy health data via chat.

## Features

- **Report Recognition**: Send checkup report photos, AI extracts and structures the data
- **Trend Tracking**: Automatically tracks indicator trends across all reports
- **Ultrasound Management**: Handles both photos and DICOM files
- **Anomaly Analysis**: Flags abnormal values with pregnancy-specific context
- **Checkup Planning**: Maintains a checkup timeline based on gestational age
- **PDF Reports**: Generate comprehensive PDF summary reports
- **Knowledge Base**: Extensible book-based reference library

## Installation

```bash
# Install from GitHub
openclaw skills install <github-url>

# Or copy manually
cp -r pregnancy-care ~/.openclaw/skills/

# Install Python dependencies (required)
pip3 install reportlab

# Optional: for DICOM support
pip3 install pydicom Pillow numpy

# Optional: for adding books to knowledge base
pip3 install ebooklib beautifulsoup4
```

## Usage

Start a conversation with your OpenClaw bot and send a pregnancy checkup report photo. The skill will guide you through setup on first use.

### Commands

- Send report photos → automatic recognition + analysis
- Send ultrasound photos or DICOM ZIP → image management
- "生成PDF报告" → comprehensive PDF report
- Ask any pregnancy question → knowledge base lookup
- Send an epub file → add to knowledge base

## Knowledge Base

The `references/books/` directory is empty by default (copyright). To add your own books:

```bash
python3 scripts/epub-to-md.py "your-book.epub" "references/books/书名/"
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

## Disclaimer

All analysis is for reference only and does not constitute medical advice. Consult your doctor for any health concerns.

## License

MIT
