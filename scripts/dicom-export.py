#!/usr/bin/env python3
"""
Extract DICOM files from a ZIP archive and export each frame as a high-quality JPG.

Usage:
    python3 dicom-export.py <input_zip_or_dir> <output_dir>

Example:
    python3 dicom-export.py ultrasound.zip pregnancy/ultrasound/2026-01-05/

Output:
    output_dir/
    ├── frame_001.jpg
    ├── frame_002.jpg
    ├── ...
    └── dicom_info.md    ← extracted DICOM metadata

Dependencies:
    pip3 install pydicom Pillow numpy
"""

import sys
import os
import zipfile
import tempfile
from pathlib import Path


def check_dependencies():
    missing = []
    try:
        import pydicom
    except ImportError:
        missing.append("pydicom")
    try:
        from PIL import Image
    except ImportError:
        missing.append("Pillow")
    try:
        import numpy
    except ImportError:
        missing.append("numpy")
    if missing:
        print(f"Error: Missing dependencies: {', '.join(missing)}")
        print(f"Install with: pip3 install {' '.join(missing)}")
        sys.exit(1)


def dicom_to_jpg(dicom_path, output_path):
    """Convert a single DICOM file to JPG."""
    import pydicom
    import numpy as np
    from PIL import Image

    try:
        ds = pydicom.dcmread(dicom_path)
        pixel_array = ds.pixel_array

        if pixel_array.max() > 0:
            normalized = (
                (pixel_array - pixel_array.min())
                / (pixel_array.max() - pixel_array.min())
                * 255
            ).astype(np.uint8)
        else:
            normalized = pixel_array.astype(np.uint8)

        if len(normalized.shape) == 3 and normalized.shape[2] == 3:
            img = Image.fromarray(normalized, "RGB")
        else:
            img = Image.fromarray(normalized, "L")

        img.save(output_path, "JPEG", quality=95)
        return True, ds
    except Exception as e:
        return False, str(e)


def extract_metadata(ds):
    """Extract useful DICOM metadata as a dict."""
    fields = {
        "PatientName": "患者姓名",
        "PatientBirthDate": "出生日期",
        "StudyDate": "检查日期",
        "Modality": "检查类型",
        "InstitutionName": "医院",
        "Manufacturer": "设备厂商",
        "ManufacturerModelName": "设备型号",
        "Rows": "图像高度",
        "Columns": "图像宽度",
    }
    result = {}
    for key, label in fields.items():
        val = getattr(ds, key, None)
        if val is not None:
            result[label] = str(val)
    return result


def process_directory(input_dir, output_dir):
    """Process all DICOM files in a directory."""
    import pydicom

    os.makedirs(output_dir, exist_ok=True)

    dicom_files = []
    for ext in ["*.dcm", "*.dic", "*.DCM", "*.DIC"]:
        dicom_files.extend(Path(input_dir).rglob(ext))

    for f in Path(input_dir).rglob("*"):
        if f.is_file() and f.suffix == "" and f.name != "DICOMDIR":
            try:
                pydicom.dcmread(f, stop_before_pixels=True)
                dicom_files.append(f)
            except Exception:
                pass

    if not dicom_files:
        print("No DICOM files found.")
        return

    dicom_files.sort()
    print(f"Found {len(dicom_files)} DICOM files")

    metadata_list = []
    for idx, dcm_path in enumerate(dicom_files, 1):
        jpg_name = f"frame_{idx:03d}.jpg"
        jpg_path = os.path.join(output_dir, jpg_name)

        success, result = dicom_to_jpg(dcm_path, jpg_path)
        if success:
            print(f"  [{idx:03d}] {dcm_path.name} -> {jpg_name}")
            if not metadata_list:
                metadata_list.append(extract_metadata(result))
        else:
            print(f"  [{idx:03d}] {dcm_path.name} FAILED: {result}")

    if metadata_list:
        info_path = os.path.join(output_dir, "dicom_info.md")
        with open(info_path, "w", encoding="utf-8") as f:
            f.write("# DICOM 影像信息\n\n")
            for key, val in metadata_list[0].items():
                f.write(f"- {key}：{val}\n")
            f.write(f"- 帧数：{len(dicom_files)}\n")
        print(f"\nMetadata saved to {info_path}")

    print(f"Done! {len(dicom_files)} frames exported to {output_dir}")


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 dicom-export.py <input_zip_or_dir> <output_dir>")
        sys.exit(1)

    check_dependencies()

    input_path = sys.argv[1]
    output_dir = sys.argv[2]

    if not os.path.exists(input_path):
        print(f"Error: Path not found: {input_path}")
        sys.exit(1)

    if zipfile.is_zipfile(input_path):
        with tempfile.TemporaryDirectory() as tmp_dir:
            print(f"Extracting ZIP: {input_path}")
            with zipfile.ZipFile(input_path, "r") as z:
                z.extractall(tmp_dir)
            process_directory(tmp_dir, output_dir)

        import shutil
        zip_dest = os.path.join(output_dir, Path(input_path).name)
        if not os.path.exists(zip_dest):
            shutil.copy2(input_path, zip_dest)
    elif os.path.isdir(input_path):
        process_directory(input_path, output_dir)
    else:
        print(f"Error: {input_path} is not a ZIP file or directory")
        sys.exit(1)


if __name__ == "__main__":
    main()
