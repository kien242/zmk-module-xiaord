#!/usr/bin/env python3
"""Convert a photo into a Xiaord 240x240 LVGL RGB565 background."""

from __future__ import annotations
import argparse
import struct
import zlib
from pathlib import Path

# Color Constants
COLOR_GREEN = "\033[92m"
COLOR_RESET = "\033[0m"

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
    size = round(crop_size)
    return left, top, size

def rgb565_bytes(pixels: list[tuple[int, int, int]]) -> bytes:
    out = bytearray()
    for r, g, b in pixels:
        value = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
        out.append(value & 0xFF)
        out.append((value >> 8) & 0xFF)
    return bytes(out)

def write_c_file(path: Path, bg_id: str, data: bytes) -> None:
    symbol = f"bg_{bg_id}_map"
    img = f"img_bg_{bg_id}"
    
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
        "};",
        "",
        f"const lv_image_dsc_t {img} = {{",
        "  .header.cf = LV_COLOR_FORMAT_RGB565,",
        "  .header.magic = LV_IMAGE_HEADER_MAGIC,",
        f"  .header.w = {SIZE},",
        f"  .header.h = {SIZE},",
        f"  .data_size = {len(data)},",
        f"  .data = {symbol},",
        "};",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")

def convert_with_pillow(source: Path, center_x: float, center_y: float, zoom: float) -> list[tuple[int, int, int]]:
    from PIL import Image, ImageOps
    img = Image.open(source)
    img = ImageOps.exif_transpose(img)
    left, top, crop_size = crop_square_box(img.size[0], img.size[1], center_x, center_y, zoom)
    square = img.crop((left, top, left + crop_size, top + crop_size))
    final = square.resize((SIZE, SIZE), Image.Resampling.LANCZOS).convert("RGB")
    return list(final.getdata())

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("bg_id", type=str, default="user_defined")
    parser.add_argument("--center-x", type=float, default=0.5)
    parser.add_argument("--center-y", type=float, default=0.5)
    parser.add_argument("--zoom", type=float, default=1.0)
    parser.add_argument("--out-dir", type=Path)
    args = parser.parse_args()

    # Bắt buộc dùng Pillow như yêu cầu
    try:
        pixels = convert_with_pillow(args.source, args.center_x, args.center_y, args.zoom)
    except ImportError:
        raise RuntimeError("Pillow is required for this conversion. Install it with: pip install pillow")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    c_path = args.out_dir / f"bg_{args.bg_id}.c"

    write_c_file(c_path, args.bg_id, rgb565_bytes(pixels))
    
    # In màu xanh duy nhất trên 1 dòng này
    print(f"{COLOR_GREEN}-- Successfully generated: {c_path}{COLOR_RESET}")

if __name__ == "__main__":
    main()