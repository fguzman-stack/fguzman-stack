#!/usr/bin/env python3
"""Generate a retro 1-bit VISUAL.MAP GIF for a GitHub profile README.

Default output is a neon-magenta particle Tux drawn with a serpentine scan.
Optionally pass --input path/to/image.png to use your own silhouette.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps


WIDTH = 300
HEIGHT = 340
BG = "#0b0f19"
PANEL = "#111827"
BORDER = "#f472b6"
DIM = "#394150"
TEXT = "#f8c7df"
MUTED = "#8b5d75"
NEON = "#ff4fb8"
NEON_HOT = "#ffd1ec"

GRID_W = 36
GRID_H = 34
CELL = 6
DOT = 2
MAP_X = 42
MAP_Y = 58


def load_font(size: int) -> ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/consola.ttf",
        "C:/Windows/Fonts/lucon.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/System/Library/Fonts/Menlo.ttc",
    ]
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


FONT_9 = load_font(9)
FONT_10 = load_font(10)
FONT_12 = load_font(12)


def tux_mask(x: float, y: float) -> bool:
    """Return True when normalized coordinates are inside a chunky Tux shape."""
    body = ((x / 0.72) ** 2 + ((y - 0.08) / 0.86) ** 2) < 1.0
    head = ((x / 0.47) ** 2 + ((y + 0.64) / 0.36) ** 2) < 1.0
    left_flipper = (((x + 0.61) / 0.22) ** 2 + ((y - 0.08) / 0.55) ** 2) < 1.0
    right_flipper = (((x - 0.61) / 0.22) ** 2 + ((y - 0.08) / 0.55) ** 2) < 1.0
    left_foot = (((x + 0.32) / 0.31) ** 2 + ((y - 0.79) / 0.16) ** 2) < 1.0
    right_foot = (((x - 0.32) / 0.31) ** 2 + ((y - 0.79) / 0.16) ** 2) < 1.0
    belly_cut = ((x / 0.42) ** 2 + ((y - 0.2) / 0.52) ** 2) < 1.0
    face_cut = ((x / 0.31) ** 2 + ((y + 0.57) / 0.21) ** 2) < 1.0
    return (body or head or left_flipper or right_flipper or left_foot or right_foot) and not (
        belly_cut or face_cut
    )


def default_points() -> list[tuple[int, int]]:
    points: list[tuple[int, int]] = []
    for gy in range(GRID_H):
        for gx in range(GRID_W):
            nx = (gx / (GRID_W - 1)) * 2 - 1
            ny = (gy / (GRID_H - 1)) * 2 - 1
            if tux_mask(nx, ny):
                points.append((gx, gy))
    return points


def points_from_image(path: Path) -> list[tuple[int, int]]:
    image = Image.open(path).convert("RGBA")
    alpha = image.getchannel("A")
    gray = ImageOps.grayscale(image)
    mask = Image.new("L", image.size, 0)
    mask.paste(gray, mask=alpha)
    mask = ImageOps.autocontrast(mask).resize((GRID_W, GRID_H), Image.Resampling.LANCZOS)
    points: list[tuple[int, int]] = []
    for gy in range(GRID_H):
        for gx in range(GRID_W):
            if mask.getpixel((gx, gy)) > 72:
                points.append((gx, gy))
    return points


def serpentine(points: list[tuple[int, int]]) -> list[tuple[int, int]]:
    point_set = set(points)
    ordered: list[tuple[int, int]] = []
    for gy in range(GRID_H):
        xs = range(GRID_W) if gy % 2 == 0 else range(GRID_W - 1, -1, -1)
        for gx in xs:
            if (gx, gy) in point_set:
                ordered.append((gx, gy))
    return ordered


def draw_corner(draw: ImageDraw.ImageDraw, x: int, y: int, sx: int, sy: int) -> None:
    size = 15
    draw.line((x, y, x + sx * size, y), fill=BORDER, width=1)
    draw.line((x, y, x, y + sy * size), fill=BORDER, width=1)


def draw_base() -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(image)
    draw.rectangle((10, 10, WIDTH - 11, HEIGHT - 11), outline=DIM, width=1)
    draw.rectangle((16, 16, WIDTH - 17, HEIGHT - 17), outline="#1f2937", width=1)
    draw_corner(draw, 20, 20, 1, 1)
    draw_corner(draw, WIDTH - 21, 20, -1, 1)
    draw_corner(draw, 20, HEIGHT - 21, 1, -1)
    draw_corner(draw, WIDTH - 21, HEIGHT - 21, -1, -1)

    draw.text((24, 28), "VISUAL.MAP", fill=TEXT, font=FONT_12)
    draw.text((213, 30), "300x340", fill=MUTED, font=FONT_9)
    draw.text((248, 30), "1-BIT", fill=BORDER, font=FONT_9)
    draw.line((24, 45, WIDTH - 25, 45), fill="#263241", width=1)

    for gx in range(0, GRID_W, 4):
        x = MAP_X + gx * CELL
        draw.line((x, MAP_Y - 6, x, MAP_Y + GRID_H * CELL + 2), fill="#111d2b", width=1)
    for gy in range(0, GRID_H, 4):
        y = MAP_Y + gy * CELL
        draw.line((MAP_X - 6, y, MAP_X + GRID_W * CELL + 2, y), fill="#111d2b", width=1)

    draw.line((24, 278, WIDTH - 25, 278), fill="#263241", width=1)
    draw.text((24, 290), "PTS 18000", fill=TEXT, font=FONT_10)
    draw.text((102, 290), "·", fill=BORDER, font=FONT_10)
    draw.text((118, 290), "FS/SERPENTINE", fill=TEXT, font=FONT_10)
    draw.text((24, 307), "SCAN LOOP: ON", fill=MUTED, font=FONT_9)
    draw.text((191, 307), "fguzman-stack", fill=BORDER, font=FONT_9)
    return image


def dot_xy(gx: int, gy: int) -> tuple[int, int]:
    return MAP_X + gx * CELL, MAP_Y + gy * CELL


def draw_frame(base: Image.Image, ordered: list[tuple[int, int]], frame: int, total: int) -> Image.Image:
    image = base.copy()
    glow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    draw = ImageDraw.Draw(image)

    progress = frame / total
    wave = (math.sin(progress * math.tau) + 1) / 2
    visible_count = int(len(ordered) * progress)
    tail = 26

    for index, (gx, gy) in enumerate(ordered):
        x, y = dot_xy(gx, gy)
        if index < visible_count:
            age = max(0, visible_count - index)
            if age < tail:
                color = NEON_HOT
                radius = DOT + 1
            else:
                color = NEON
                radius = DOT
            glow_draw.ellipse((x - 4, y - 4, x + 4, y + 4), fill=(255, 79, 184, 45))
            draw.rectangle((x - radius, y - radius, x + radius, y + radius), fill=color)
        else:
            draw.point((x, y), fill="#352136")

    scan_index = min(visible_count, len(ordered) - 1)
    if ordered:
        sx, sy = dot_xy(*ordered[scan_index])
        draw.rectangle((sx - 6, sy - 6, sx + 6, sy + 6), outline=NEON_HOT, width=1)
        draw.line((MAP_X - 10, sy, MAP_X + GRID_W * CELL + 6, sy), fill="#3b2942", width=1)

    noise_y = int(MAP_Y + wave * GRID_H * CELL)
    draw.line((30, noise_y, WIDTH - 31, noise_y), fill="#182033", width=1)

    blurred = glow.filter(ImageFilter.GaussianBlur(3))
    image = Image.alpha_composite(image.convert("RGBA"), blurred)
    image = Image.alpha_composite(image, glow)
    return image.convert("P", palette=Image.Palette.ADAPTIVE, colors=64)


def generate(points: list[tuple[int, int]], output: Path, frames: int, duration: int) -> None:
    ordered = serpentine(points)
    base = draw_base()
    images = [draw_frame(base, ordered, frame, frames) for frame in range(frames)]
    output.parent.mkdir(parents=True, exist_ok=True)
    images[0].save(
        output,
        save_all=True,
        append_images=images[1:],
        duration=duration,
        loop=0,
        optimize=True,
        disposal=2,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a VISUAL.MAP retro GIF.")
    parser.add_argument("--input", type=Path, help="Optional logo/image used as the particle mask.")
    parser.add_argument("--output", type=Path, default=Path("assets/visual-map-tux.gif"))
    parser.add_argument("--frames", type=int, default=72)
    parser.add_argument("--duration", type=int, default=45, help="Frame duration in ms.")
    args = parser.parse_args()

    points = points_from_image(args.input) if args.input else default_points()
    if not points:
        raise SystemExit("No points found. Try an image with more contrast or alpha.")
    generate(points, args.output, args.frames, args.duration)
    print(f"Generated {args.output} ({len(points)} particles, {args.frames} frames)")


if __name__ == "__main__":
    main()
