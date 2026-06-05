#!/usr/bin/env python3
"""
医疗报告图片预处理 —— 为视觉识别准备一张"看得清"的图。

设计目标：手机拍的化验单/报告普遍是低清、歪斜、反光、低对比。直接整页硬读
会把数字/项目名认错（实测：血钾 K+ 被认成葡萄糖 GLU）。本脚本把原图机械地
矫正+放大+增强，输出无损 PNG 供模型二次视觉精读。

方向（90°/180°/270°）由调用方（视觉模型先扫一眼原图）通过 --rotate 给出；
脚本只做机械处理，不猜大方向。小角度歪斜由投影法自动纠正。

依赖：Pillow numpy（openclaw runtime 已具备）。opencv 可选，装了则用更稳的纠偏。

用法：
    # 体检：先看清晰度/分辨率够不够，不够就让用户重拍
    python3 preprocess-image.py <img> --probe

    # 矫正增强（模型判断原图被顺时针拍歪了 90°，故逆时针转回）
    python3 preprocess-image.py <img> <out.png> --rotate 90

    # 只裁某区域放大精读（坐标用 0~1 比例：左,上,右,下）
    python3 preprocess-image.py <img> <out.png> --rotate 90 --crop 0.5,0.3,1.0,0.6

--probe 输出 JSON：
    {"width","height","long_edge","blur_var","low_res","blurry","advice"}
    low_res: 长边 < 2200（密集化验单建议 ≥2600）
    blurry : 拉普拉斯方差 < 120（越小越糊）
"""

import sys
import json
import argparse
from pathlib import Path


def _lap_var(gray_arr):
    """拉普拉斯方差，衡量清晰度（越大越锐）。纯 numpy 实现，无需 opencv。"""
    import numpy as np
    a = gray_arr.astype("float32")
    # 3x3 拉普拉斯核卷积（手写，避免 scipy 依赖）
    lap = (
        -4 * a
        + np.roll(a, 1, 0) + np.roll(a, -1, 0)
        + np.roll(a, 1, 1) + np.roll(a, -1, 1)
    )
    # 去掉因 roll 产生的边界回卷
    lap = lap[1:-1, 1:-1]
    return float(lap.var())


def _estimate_skew(gray_arr, limit=8.0, step=0.5):
    """投影法估计小角度歪斜：在 ±limit° 内找让水平投影方差最大的角度。"""
    import numpy as np
    from PIL import Image

    # 缩小到长边 ~1000 加速；二值化（低于均值算前景）
    h, w = gray_arr.shape
    scale = 1000.0 / max(h, w)
    if scale < 1.0:
        small = np.array(
            Image.fromarray(gray_arr).resize(
                (max(1, int(w * scale)), max(1, int(h * scale)))
            )
        )
    else:
        small = gray_arr
    binary = (small < small.mean()).astype("float32")

    best_angle, best_score = 0.0, -1.0
    base = Image.fromarray((binary * 255).astype("uint8"))
    a = -limit
    while a <= limit + 1e-9:
        rot = np.array(
            base.rotate(a, resample=Image.BILINEAR, fillcolor=0)
        ).astype("float32") / 255.0
        proj = rot.sum(axis=1)            # 每行前景像素数
        score = float(((proj[1:] - proj[:-1]) ** 2).sum())  # 行间差分方差→文字行越齐越大
        if score > best_score:
            best_score, best_angle = score, a
        a += step
    return best_angle


def main():
    ap = argparse.ArgumentParser(description="医疗报告图片预处理")
    ap.add_argument("input")
    ap.add_argument("output", nargs="?", help="输出 PNG 路径（--probe 时可省略）")
    ap.add_argument("--rotate", type=int, default=0, choices=[0, 90, 180, 270],
                    help="先逆时针旋转的角度（由视觉模型判断原图方向后给出）")
    ap.add_argument("--crop", default=None,
                    help="裁剪区域比例 左,上,右,下（0~1），用于放大精读某列/某区")
    ap.add_argument("--no-deskew", action="store_true", help="跳过小角度纠偏")
    ap.add_argument("--min-long-edge", type=int, default=3000,
                    help="升采样目标：长边像素下限")
    ap.add_argument("--probe", action="store_true", help="只做清晰度/分辨率体检，输出 JSON")
    args = ap.parse_args()

    try:
        from PIL import Image, ImageOps, ImageFilter
        import numpy as np
    except ImportError as e:
        print(json.dumps({"error": f"缺依赖: {e}. 安装: pip3 install pillow numpy"}),
              file=sys.stderr)
        sys.exit(3)

    src = Path(args.input)
    if not src.is_file():
        print(json.dumps({"error": f"找不到输入: {src}"}), file=sys.stderr)
        sys.exit(4)

    im = ImageOps.exif_transpose(Image.open(src))  # 尊重 EXIF 方向

    # ---- 体检模式 ----
    if args.probe:
        gray = np.array(im.convert("L"))
        long_edge = max(im.size)
        blur = _lap_var(gray)
        low_res = long_edge < 2200
        blurry = blur < 120
        advice = []
        if low_res:
            advice.append("分辨率偏低，密集化验单建议重拍并靠近、填满取景框")
        if blurry:
            advice.append("画面偏糊，重拍时对焦清晰、避免手抖/反光")
        print(json.dumps({
            "width": im.size[0], "height": im.size[1],
            "long_edge": long_edge, "blur_var": round(blur, 1),
            "low_res": low_res, "blurry": blurry,
            "ok": not (low_res or blurry),
            "advice": advice,
        }, ensure_ascii=False))
        return

    if not args.output:
        print(json.dumps({"error": "非 --probe 模式必须给 output 路径"}), file=sys.stderr)
        sys.exit(2)

    # ---- 处理流水线 ----
    if args.rotate:
        im = im.rotate(args.rotate, expand=True)

    gray = im.convert("L")
    arr = np.array(gray)

    if not args.no_deskew:
        try:
            angle = _estimate_skew(arr)
            if abs(angle) >= 0.5:
                gray = gray.rotate(angle, resample=Image.BICUBIC,
                                   expand=True, fillcolor=255)
        except Exception:
            pass  # 纠偏失败不致命，继续

    # 升采样到目标长边
    w, h = gray.size
    long_edge = max(w, h)
    if long_edge < args.min_long_edge:
        f = args.min_long_edge / long_edge
        gray = gray.resize((int(w * f), int(h * f)), Image.LANCZOS)

    gray = ImageOps.autocontrast(gray, cutoff=1)
    gray = gray.filter(ImageFilter.UnsharpMask(radius=2, percent=160, threshold=2))

    if args.crop:
        try:
            x0, y0, x1, y1 = (float(v) for v in args.crop.split(","))
            W, H = gray.size
            box = (int(W * x0), int(H * y0), int(W * x1), int(H * y1))
            gray = gray.crop(box)
            # 裁完再放大一次，便于精读小字
            gray = gray.resize((gray.width * 2, gray.height * 2), Image.LANCZOS)
        except Exception as e:
            print(json.dumps({"error": f"--crop 解析失败: {e}"}), file=sys.stderr)
            sys.exit(2)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    gray.save(str(out), "PNG")
    print(json.dumps({"output": str(out), "size": list(gray.size)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
