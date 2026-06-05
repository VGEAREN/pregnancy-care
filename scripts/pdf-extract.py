#!/usr/bin/env python3
"""
把 PDF 报告渲染成高清图（主）+ 抽取文字层（辅，仅交叉校验）。

为什么默认走图：医疗报告（化验单/体检/影像）多为表格密集件或扫描件。
- 扫描件根本没有文字层，get_text() 返回空 —— 只有图里有数据。
- 数字 PDF 的文字层把表格拍扁成字符流，数值列和参考范围列会错位，
  导致"数值匹配到错误的参考范围"且静默不报。
所以**以每页高清 PNG 为准用视觉精读**，extracted.txt 仅作交叉对照，绝不单独采信。

用法：
    python3 pdf-extract.py <input_pdf> <output_dir> [--dpi 300]

输出：
    output_dir/
    ├── pages/page_001.png     ← 主：每页 300DPI 无损图，供视觉逐行精读
    ├── pages/page_002.png
    ├── extracted.txt          ← 辅：文字层（扫描页为空），仅交叉校验
    └── _pdfmeta.json          ← 每页有无文字层 / 是否扫描件 / 尺寸

stdout 打印 JSON 摘要，其中 image_only_pages 列出"无文字层、必须视觉读"的页码。

依赖：pip3 install pymupdf
说明：用 PNG 而非 JPEG —— 文字/表线是高频边缘，JPEG 有损压缩会糊化小数字；
PNG 无损，体检报告这种线条图通常还更小。
"""

import sys
import json
import argparse
from pathlib import Path


def extract_pdf(input_pdf, output_dir, dpi=300):
    """渲染每页为高清 PNG（主）+ 抽取文字层（辅）。返回 meta dict。

    可被测试/其他脚本直接 import 调用。
    """
    import fitz  # PyMuPDF

    input_pdf = Path(input_pdf)
    out_dir = Path(output_dir)
    pages_dir = out_dir / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(str(input_pdf))
    text_parts = []
    meta_pages = []
    image_only = []

    for i, page in enumerate(doc, start=1):
        page_text = page.get_text().strip()
        text_parts.append(f"=== Page {i} ===\n{page_text}")

        pix = page.get_pixmap(dpi=dpi)
        png_path = pages_dir / f"page_{i:03d}.png"
        pix.save(str(png_path), "png")

        has_text = len(page_text) >= 10  # 文字层基本为空 → 扫描件，必须视觉读
        if not has_text:
            image_only.append(i)
        meta_pages.append({
            "page": i, "image": str(png_path),
            "has_text_layer": has_text,
            "text_chars": len(page_text),
            "px": [pix.width, pix.height],
        })

    n = doc.page_count
    doc.close()

    (out_dir / "extracted.txt").write_text("\n".join(text_parts), encoding="utf-8")
    meta = {
        "source": str(input_pdf), "pages": n, "dpi": dpi,
        "pages_dir": str(pages_dir),
        "image_only_pages": image_only,
        "page_meta": meta_pages,
        "note": "以 pages/*.png 视觉精读为准；extracted.txt 仅交叉校验，勿单独采信",
    }
    (out_dir / "_pdfmeta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return meta


def main():
    ap = argparse.ArgumentParser(description="PDF 渲染高清图 + 文字层抽取")
    ap.add_argument("input")
    ap.add_argument("output_dir")
    ap.add_argument("--dpi", type=int, default=300,
                    help="渲染分辨率，默认 300（OCR 基线；密集小字可上 400）")
    args = ap.parse_args()

    try:
        import fitz  # noqa: F401  仅用于提前给出清晰的缺依赖提示
    except ImportError:
        print(json.dumps({"error": "缺依赖 pymupdf。安装: pip3 install pymupdf"},
                         ensure_ascii=False), file=sys.stderr)
        sys.exit(3)

    src = Path(args.input)
    if not src.is_file():
        print(json.dumps({"error": f"输入文件不存在 (input not found): {src}"},
                         ensure_ascii=False), file=sys.stderr)
        sys.exit(4)

    try:
        meta = extract_pdf(src, args.output_dir, dpi=args.dpi)
    except Exception as e:
        print(json.dumps({"error": f"PDF 处理失败（可能加密/损坏）: {e}"},
                         ensure_ascii=False), file=sys.stderr)
        sys.exit(5)

    print(json.dumps({
        "pages": meta["pages"], "dpi": meta["dpi"],
        "pages_dir": meta["pages_dir"],
        "image_only_pages": meta["image_only_pages"],
        "ok": True,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
