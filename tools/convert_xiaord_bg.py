#!/usr/bin/env python3
"""Convert a photo into a Xiaord 240x240 LVGL RGB565 background."""

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
    size = round(crop_size)
    return left, top, size

def rgb565_bytes(pixels: list[tuple[int, int, int]]) -> bytes:
    out = bytearray()
    for r, g, b in pixels:
        value = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
        out.append(value & 0xFF)
        out.append((value >> 8) & 0xFF)
    return bytes(out)

def paeth_predictor(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    if pa <= pb and pa <= pc: return a
    if pb <= pc: return b
    return c

def read_png_rgb(path: Path) -> tuple[int, int, list[tuple[int, int, int]]]:
    data = path.read_bytes()
    if not data.startswith(PNG_SIG): raise ValueError("not a PNG file")
    pos = len(PNG_SIG)
    width = height = color_type = bit_depth = interlace = None
    idat = bytearray()
    while pos < len(data):
        length = struct.unpack(">I", data[pos : pos + 4])[0]
        pos += 4
        chunk_type = data[pos : pos + 4]
        pos += 4
        chunk = data[pos : pos + length]
        pos += length + 4
        if chunk_type == b"IHDR":
            width, height, bit_depth, color_type, _, _, interlace = struct.unpack(">IIBBBBB", chunk)
        elif chunk_type == b"IDAT": idat.extend(chunk)
        elif chunk_type == b"IEND": break

    if width is None or height is None: raise ValueError("missing PNG IHDR")
    if bit_depth != 8 or color_type not in (2, 6) or interlace != 0:
        raise ValueError("Only non-interlaced 8-bit RGB/RGBA PNG supported without Pillow")

    channels = 4 if color_type == 6 else 3
    stride = width * channels
    raw = zlib.decompress(bytes(idat))
    rows = []
    src = 0
    for _y in range(height):
        filter_type = raw[src]
        src += 1
        row = bytearray(raw[src : src + stride])
        src += stride
        prev = rows[-1] if rows else bytearray(stride)
        for x in range(stride):
            left = row[x - channels] if x >= channels else 0
            up = prev[x]
            up_left = prev[x - channels] if x >= channels else 0
            if filter_type == 1: row[x] = (row[x] + left) & 0xFF
            elif filter_type == 2: row[x] = (row[x] + up) & 0xFF
            elif filter_type == 3: row[x] = (row[x] + ((left + up) // 2)) & 0xFF
            elif filter_type == 4: row[x] = (row[x] + paeth_predictor(left, up, up_left)) & 0xFF
        rows.append(row)

    pixels = []
    for row in rows:
        for x in range(0, stride, channels):
            pixels.append((row[x], row[x + 1], row[x + 2]))
    return width, height, pixels

def crop_resize_rgb(width, height, pixels, center_x, center_y, zoom):
    left, top, crop_size = crop_square_box(width, height, center_x, center_y, zoom)
    out = []
    for y in range(SIZE):
        src_y = top + min(crop_size - 1, int(y * crop_size / SIZE))
        row_base = src_y * width
        for x in range(SIZE):
            src_x = left + min(crop_size - 1, int(x * crop_size / SIZE))
            out.append(pixels[row_base + src_x])
    return out

def png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    import binascii
    crc = binascii.crc32(chunk_type)
    crc = binascii.crc32(data, crc) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + chunk_type + data + struct.pack(">I", crc)

def write_png_rgb(path: Path, pixels: list[tuple[int, int, int]]) -> None:
    rows = bytearray()
    for y in range(SIZE):
        rows.append(0)
        for r, g, b in pixels[y * SIZE : (y + 1) * SIZE]:
            rows.extend((r, g, b))
    ihdr = struct.pack(">IIBBBBB", SIZE, SIZE, 8, 2, 0, 0, 0)
    path.write_bytes(PNG_SIG + png_chunk(b"IHDR", ihdr) + png_chunk(b"IDAT", zlib.compress(bytes(rows), 9)) + png_chunk(b"IEND", b""))

def write_c_file(path: Path, bg_id: str, data: bytes) -> None:
    symbol = f"bg_{bg_id}_map"
    img = f"img_bg_{bg_id}"
    lines = [
        '#include "lvgl.h"',
        "",
        f"const uint8_t {symbol}[] = {{",
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
        "};",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")

def write_rgb565_file(path: Path, pixels: list[tuple[int, int, int]]) -> None:
    path.write_bytes(rgb565_bytes(pixels))

def convert_with_pillow(source: Path, center_x: float, center_y: float, zoom: float) -> list[tuple[int, int, int]] | None:
    try:
        from PIL import Image, ImageOps
    except ModuleNotFoundError: return None
    img = Image.open(source)
    img = ImageOps.exif_transpose(img)
    left, top, crop_size = crop_square_box(img.size[0], img.size[1], center_x, center_y, zoom)
    square = img.crop((left, top, left + crop_size, top + crop_size))
    final = square.resize((SIZE, SIZE), Image.Resampling.LANCZOS).convert("RGB")
    return list(final.getdata())

def convert_source(source: Path, center_x: float, center_y: float, zoom: float) -> list[tuple[int, int, int]]:
    pixels = convert_with_pillow(source, center_x, center_y, zoom)
    if pixels is not None: return pixels
    if source.suffix.lower() == ".png":
        width, height, png_pixels = read_png_rgb(source)
        return crop_resize_rgb(width, height, png_pixels, center_x, center_y, zoom)
    raise RuntimeError("Pillow required for JPG. Use PNG for GitHub Actions.")

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("bg_id", type=str)
    parser.add_argument("--center-x", type=float, default=0.5)
    parser.add_argument("--center-y", type=float, default=0.5)
    parser.add_argument("--zoom", type=float, default=1.0)
    parser.add_argument("--out-dir", type=Path)
    parser.add_argument("--rgb565-out", type=Path)
    args = parser.parse_args()

    pixels = convert_source(args.source, args.center_x, args.center_y, args.zoom)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    
    write_png_rgb(args.out_dir / f"bg_{args.bg_id}.png", pixels)
    write_c_file(args.out_dir / f"bg_{args.bg_id}.c", args.bg_id, rgb565_bytes(pixels))

    if args.rgb565_out:
        args.rgb565_out.parent.mkdir(parents=True, exist_ok=True)
        write_rgb565_file(args.rgb565_out, pixels)

if __name__ == "__main__":
    main()