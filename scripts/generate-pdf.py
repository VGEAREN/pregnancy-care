#!/usr/bin/env python3
"""
Generate a comprehensive pregnancy checkup PDF report.

Usage:
    python3 generate-pdf.py <pregnancy_dir> [output_path]

Example:
    python3 generate-pdf.py pregnancy/
    python3 generate-pdf.py pregnancy/ pregnancy/report_20260316.pdf

Reads:
    pregnancy/profile.md    — basic info
    pregnancy/summary.md    — trends and checkup plan
    pregnancy/records/*.md  — all structured reports

Dependencies:
    pip3 install reportlab
"""

import sys
import os
import re
from datetime import date
from pathlib import Path


def check_dependencies():
    try:
        import reportlab
    except ImportError:
        print("Error: Missing dependency: reportlab")
        print("Install with: pip3 install reportlab")
        sys.exit(1)


def parse_markdown_table(text):
    """Parse a Markdown table into a list of dicts."""
    lines = [l.strip() for l in text.strip().split("\n") if l.strip()]
    if len(lines) < 2:
        return []

    header_line = None
    data_start = 0
    for i, line in enumerate(lines):
        if "|" in line and set(line.replace("|", "").replace("-", "").replace(":", "").strip()) == set():
            if i > 0:
                header_line = lines[i - 1]
                data_start = i + 1
            break

    if header_line is None and len(lines) >= 2:
        header_line = lines[0]
        data_start = 2

    if header_line is None:
        return []

    headers = [h.strip() for h in header_line.split("|") if h.strip()]
    rows = []
    for line in lines[data_start:]:
        cols = [c.strip() for c in line.split("|") if c.strip()]
        if cols:
            row = {}
            for j, h in enumerate(headers):
                row[h] = cols[j] if j < len(cols) else ""
            rows.append(row)

    return rows


def read_file(path):
    """Read a file and return its content, or empty string if not found."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""


def extract_profile(content):
    """Extract key-value pairs from profile.md."""
    info = {}
    for line in content.split("\n"):
        match = re.match(r"^-\s*(.+?)：(.+)$", line.strip())
        if match:
            info[match.group(1).strip()] = match.group(2).strip()
    return info


def extract_sections(content):
    """Split Markdown content into sections by ## headings."""
    sections = {}
    current_title = None
    current_lines = []
    for line in content.split("\n"):
        match = re.match(r"^##\s+(.+)$", line)
        if match:
            if current_title:
                sections[current_title] = "\n".join(current_lines)
            current_title = match.group(1).strip()
            current_lines = []
        else:
            current_lines.append(line)
    if current_title:
        sections[current_title] = "\n".join(current_lines)
    return sections


def generate_pdf(pregnancy_dir, output_path):
    """Generate the PDF report."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
        PageBreak,
    )
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    # Try to register a Chinese font
    chinese_font = "Helvetica"
    chinese_font_paths = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    ]
    for font_path in chinese_font_paths:
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont("ChineseFont", font_path, subfontIndex=0))
                chinese_font = "ChineseFont"
                break
            except Exception:
                continue

    # Read data
    profile_content = read_file(os.path.join(pregnancy_dir, "profile.md"))
    summary_content = read_file(os.path.join(pregnancy_dir, "summary.md"))
    profile = extract_profile(profile_content)
    summary_sections = extract_sections(summary_content)

    records_dir = os.path.join(pregnancy_dir, "records")
    record_files = sorted(Path(records_dir).glob("*.md")) if os.path.isdir(records_dir) else []

    # Setup PDF
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=25 * mm,
        bottomMargin=20 * mm,
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        "ChTitle", fontName=chinese_font, fontSize=22, leading=30,
        alignment=1, spaceAfter=20
    ))
    styles.add(ParagraphStyle(
        "ChHeading", fontName=chinese_font, fontSize=14, leading=20,
        spaceAfter=10, spaceBefore=15, textColor=colors.HexColor("#2c3e50")
    ))
    styles.add(ParagraphStyle(
        "ChBody", fontName=chinese_font, fontSize=10, leading=16, spaceAfter=6
    ))
    styles.add(ParagraphStyle(
        "ChSmall", fontName=chinese_font, fontSize=8, leading=12,
        textColor=colors.grey
    ))

    story = []

    # Page 1: Cover + profile
    story.append(Spacer(1, 40 * mm))
    story.append(Paragraph("孕期产检综合报告", styles["ChTitle"]))
    story.append(Spacer(1, 10 * mm))

    today = date.today().strftime("%Y-%m-%d")
    cover_info = [
        f"姓名：{profile.get('姓名', '-')}",
        f"年龄：{profile.get('年龄', '-')}",
        f"预产期：{profile.get('预产期', '-')}",
        f"报告生成日期：{today}",
        f"报告数量：{len(record_files)} 份",
    ]
    for line in cover_info:
        story.append(Paragraph(line, styles["ChBody"]))

    story.append(PageBreak())

    # Page 2+: Trends from summary.md
    story.append(Paragraph("指标趋势", styles["ChTitle"]))

    for section_title, section_content in summary_sections.items():
        if "趋势" in section_title:
            story.append(Paragraph(section_title, styles["ChHeading"]))
            rows = parse_markdown_table(section_content)
            if rows:
                headers = list(rows[0].keys())
                table_data = [headers]
                for row in rows:
                    table_data.append([row.get(h, "") for h in headers])

                t = Table(table_data, repeatRows=1)
                t.setStyle(TableStyle([
                    ("FONTNAME", (0, 0), (-1, -1), chinese_font),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#3498db")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#ecf0f1")]),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]))
                story.append(t)
                story.append(Spacer(1, 5 * mm))
            else:
                story.append(Paragraph("暂无数据", styles["ChSmall"]))

    # Checkup plan
    if "产检计划" in summary_sections:
        story.append(PageBreak())
        story.append(Paragraph("产检计划", styles["ChTitle"]))
        plan_lines = summary_sections["产检计划"].strip().split("\n")
        for line in plan_lines:
            line = line.strip()
            if line.startswith("- [x]"):
                story.append(Paragraph(f"✅ {line[5:].strip()}", styles["ChBody"]))
            elif line.startswith("- [ ]"):
                story.append(Paragraph(f"⬜ {line[5:].strip()}", styles["ChBody"]))
            elif line.startswith("###"):
                story.append(Paragraph(line.lstrip("#").strip(), styles["ChHeading"]))
            elif line:
                story.append(Paragraph(line, styles["ChBody"]))

    # Individual records summary
    if record_files:
        story.append(PageBreak())
        story.append(Paragraph("产检记录明细", styles["ChTitle"]))

        for rec_path in record_files:
            rec_content = read_file(rec_path)
            rec_sections = extract_sections(rec_content)
            rec_name = rec_path.stem

            story.append(Paragraph(rec_name, styles["ChHeading"]))

            if "基本信息" in rec_sections:
                for line in rec_sections["基本信息"].strip().split("\n"):
                    line = line.strip()
                    if line.startswith("-"):
                        story.append(Paragraph(line, styles["ChBody"]))

            if "检查指标" in rec_sections:
                rows = parse_markdown_table(rec_sections["检查指标"])
                if rows:
                    headers = list(rows[0].keys())
                    table_data = [headers]
                    for row in rows:
                        table_data.append([row.get(h, "") for h in headers])

                    t = Table(table_data, repeatRows=1)
                    t.setStyle(TableStyle([
                        ("FONTNAME", (0, 0), (-1, -1), chinese_font),
                        ("FONTSIZE", (0, 0), (-1, -1), 7),
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#27ae60")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("TOPPADDING", (0, 0), (-1, -1), 3),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ]))
                    story.append(t)
                    story.append(Spacer(1, 3 * mm))

            if "异常分析" in rec_sections:
                analysis = rec_sections["异常分析"].strip()
                if analysis:
                    story.append(Paragraph("异常分析：", styles["ChBody"]))
                    for line in analysis.split("\n"):
                        line = line.strip()
                        if line:
                            story.append(Paragraph(line, styles["ChSmall"]))

            story.append(Spacer(1, 5 * mm))

    # Footer
    story.append(Spacer(1, 10 * mm))
    story.append(Paragraph(
        "以上报告由 AI 自动生成，仅供参考，不构成医学建议。请咨询专业医生。",
        styles["ChSmall"],
    ))

    doc.build(story)
    print(f"PDF generated: {output_path}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 generate-pdf.py <pregnancy_dir> [output_path]")
        sys.exit(1)

    check_dependencies()

    pregnancy_dir = sys.argv[1]
    if not os.path.isdir(pregnancy_dir):
        print(f"Error: Directory not found: {pregnancy_dir}")
        sys.exit(1)

    if len(sys.argv) >= 3:
        output_path = sys.argv[2]
    else:
        today = date.today().strftime("%Y%m%d")
        output_path = os.path.join(pregnancy_dir, f"孕期产检综合报告_{today}.pdf")

    generate_pdf(pregnancy_dir, output_path)


if __name__ == "__main__":
    main()
