#!/usr/bin/env python3
"""
Convert a photo into a Xiaord 240x240 LVGL RGB565 background.
Updated to support CMake auto-build and custom manual conversion.
"""

from __future__ import annotations
import argparse
import struct
import zlib
from pathlib import Path

SIZE = 240
PNG_SIG = b"\x89PNG\r\n\x1a\n"

def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))

def crop_square_box(width: int, height: int, center_x: float, center_y: float, zoom: float) -> tuple[int, int, int]:
    crop_size = min(width, height) / zoom
    crop_size = clamp(crop_size, 1, min(width, height))
    cx = clamp(center_x, 0.0, 1.0) * width
    cy = clamp(center_y, 0.0, 1.0) * height
    left = round(clamp(cx - crop_size / 2, 0, width - crop_size))
    top = round(clamp(cy - crop_size / 2, 0, height - crop_size))
    return left, top, round(crop_size)

def rgb565_bytes(pixels: list[tuple[int, int, int]]) -> bytes:
    out = bytearray()
    for r, g, b in pixels:
        value = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
        out.append(value & 0xFF)
        out.append((value >> 8) & 0xFF)
    return bytes(out)

def write_c_file(path: Path, bg_id: str, data: bytes) -> None:
    # Đã sửa: Đồng bộ tên biến và cấu trúc theo chuẩn 'defined'
    clean_id = "bg_user_defined"
    
    symbol = f"{clean_id}_map"
    img = f"img_{clean_id}"

    lines = [
        "#include \"lvgl.h\"",
        "",
        "#ifndef LV_ATTRIBUTE_MEM_ALIGN",
        "#define LV_ATTRIBUTE_MEM_ALIGN",
        "#endif",
        "",
        f"const LV_ATTRIBUTE_MEM_ALIGN uint8_t {symbol}[] = {{",
    ]
    for i in range(0, len(data), 16):
        chunk = data[i : i + 16]
        lines.append("  " + ", ".join(f"0x{b:02x}" for b in chunk) + ",")
    lines.extend([
        "};", "",
        f"const lv_image_dsc_t {img} = {{",
        "  .header.cf = LV_COLOR_FORMAT_RGB565,",
        "  .header.magic = LV_IMAGE_HEADER_MAGIC,",
        f"  .header.w = {SIZE},",
        f"  .header.h = {SIZE},",
        f"  .data_size = {len(data)},",
        f"  .data = {symbol},",
        "};"
    ])
    path.write_text("\n".join(lines), encoding="utf-8")

def convert_with_pillow(source: Path, center_x: float, center_y: float, zoom: float) -> list[tuple[int, int, int]] | None:
    try:
        from PIL import Image, ImageOps
        img = Image.open(source).convert("RGB")
        img = ImageOps.exif_transpose(img)
        w, h = img.size
        left, top, size = crop_square_box(w, h, center_x, center_y, zoom)
        final = img.crop((left, top, left + size, top + size)).resize((SIZE, SIZE), 3)
        return list(final.getdata())
    except Exception as e:
        print(f"Pillow conversion failed: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Convert photo to Xiaord background")
    parser.add_argument("source", type=Path, help="Path to bg_user_defined.png")
    # bg_id là tham số tùy chọn để "nuốt" số 4 từ CMake truyền vào mà không gây lỗi
    parser.add_argument("bg_id", type=str, nargs="?", default="bg_user_defined")
    parser.add_argument("--out-dir", type=Path, default=Path("src/display/ui/bg"))
    parser.add_argument("--center-x", type=float, default=0.5)
    parser.add_argument("--center-y", type=float, default=0.5)
    parser.add_argument("--zoom", type=float, default=1.0)
    args = parser.parse_args()

    if not args.source.exists():
        raise FileNotFoundError(f"Source file not found: {args.source}")

    pixels = convert_with_pillow(args.source, args.center_x, args.center_y, args.zoom)
    if not pixels:
        raise RuntimeError("Pillow is required for this conversion. Install it with: pip install pillow")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    
    # Đã sửa: Tên file xuất ra là bg_user_defined.c
    c_path = args.out_dir / "bg_user_defined.c"
    
    # Gọi hàm ghi file với ID chuẩn
    write_c_file(c_path, "bg_user_defined", rgb565_bytes(pixels))
    print(f"-- Successfully generated: {c_path}")

if __name__ == "__main__":
    main()