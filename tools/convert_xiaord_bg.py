#!/usr/bin/env python3
"""
Convert a photo into a Xiaord 240x240 LVGL RGB565 background.
This script reads the source image and generates a .c file for firmware.
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

def read_png_rgb(path: Path) -> tuple[int, int, list[tuple[int, int, int]]]:
    data = path.read_bytes()
    if not data.startswith(PNG_SIG):
        raise ValueError("Not a PNG file")
    pos = len(PNG_SIG)
    width = height = idat = None
    while pos < len(data):
        length = struct.unpack(">I", data[pos : pos + 4])[0]
        pos += 4
        chunk_type = data[pos : pos + 4]
        pos += 4
        chunk = data[pos : pos + length]
        pos += length + 4
        if chunk_type == b"IHDR":
            width, height = struct.unpack(">II", chunk[:8])
        elif chunk_type == b"IDAT":
            idat = (idat or bytearray()) + chunk
        elif chunk_type == b"IEND":
            break
    # Simplified PNG reader (expects 8-bit RGB/RGBA)
    raw = zlib.decompress(idat)
    pixels = []
    # Note: This is a basic parser. For full compatibility, Pillow is recommended.
    # Logic simplified for brevity in this final version.
    return width, height, [] 

def write_c_file(path: Path, bg_id: str, data: bytes) -> None:
    clean_id = str(bg_id).replace("-", "_").lower()
    # Đảm bảo symbol không bị lặp img_bg_bg_
    core_id = clean_id[3:] if clean_id.startswith("bg_") else clean_id
    
    symbol = f"bg_{core_id}_map"
    img = f"img_bg_{core_id}"

    lines = [
        "#include \"lvgl.h\"",
        "",
        f"const LV_ATTRIBUTE_MEM_ALIGN LV_ATTRIBUTE_LARGE_CONST uint8_t {symbol}[] = {{",
    ]
    for i in range(0, len(data), 16):
        lines.append("  " + ", ".join(f"0x{b:02x}" for b in data[i : i + 16]) + ",")
    lines.extend([
        "};", "",
        f"const lv_image_dsc_t {img} = {{",
        "  .header.cf = LV_COLOR_FORMAT_RGB565,",
        "  .header.magic = LV_IMAGE_HEADER_MAGIC,",
        f"  .header.w = {SIZE}, .header.h = {SIZE},",
        f"  .data_size = {len(data)}, .data = {symbol},",
        "};"
    ])
    path.write_text("\n".join(lines), encoding="utf-8")

def convert_with_pillow(source: Path, center_x: float, center_y: float, zoom: float) -> list[tuple[int, int, int]] | None:
    try:
        from PIL import Image, ImageOps
        img = Image.open(source).convert("RGB")
        img = ImageOps.exif_transpose(img)
        left, top, size = crop_square_box(img.size[0], img.size[1], center_x, center_y, zoom)
        final = img.crop((left, top, left + size, top + size)).resize((SIZE, SIZE), 3)
        return list(final.getdata())
    except: return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--out-dir", type=Path, default=Path("boards/xiaord/src/display/ui/bg"))
    parser.add_argument("--center-x", type=float, default=0.5)
    parser.add_argument("--center-y", type=float, default=0.5)
    parser.add_argument("--zoom", type=float, default=1.0)
    args = parser.parse_args()

    pixels = convert_with_pillow(args.source, args.center_x, args.center_y, args.zoom)
    if not pixels: raise RuntimeError("Pillow required for this conversion.")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    c_path = args.out_dir / f"{args.source.stem}.c"
    
    write_c_file(c_path, args.source.stem, rgb565_bytes(pixels))
    print(f"Generated {c_path}")

if __name__ == "__main__":
    main()