#!/usr/bin/env python3
"""Generate a retro VISUAL.MAP GIF for a GitHub profile README.

The default animation is an original 1-bit/terminal inspired particle map of
Tux with a continuous serpentine scanner. You can also pass --input to convert
your own logo/image into the same animated particle map.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps


WIDTH = 300
HEIGHT = 340

BG = "#0b0f19"
PANEL = "#0f1625"
GRID = "#172235"
GRID_HOT = "#26364f"
BORDER = "#ff4fb8"
TEXT = "#ffd1ec"
MUTED = "#8b5d75"
NEON = "#ff4fb8"
NEON_SOFT = "#bf2f86"
NEON_DIM = "#4a203a"
HOT = "#fff0fa"
CYAN = "#67e8f9"
AMBER = "#fbbf24"

MAP_X = 34
MAP_Y = 55
CELL = 4
GRID_W = 58
GRID_H = 54
DOT = 1


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


FONT_8 = load_font(8)
FONT_9 = load_font(9)
FONT_10 = load_font(10)
FONT_12 = load_font(12)


def layer(size: int = 240) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    return image, ImageDraw.Draw(image)


def draw_default_tux_mask(size: int = 240) -> Image.Image:
    """Build a detailed, original Tux-ish mask using vector primitives.

    Colors encode particle groups:
    magenta = shell/body, pink = belly/face cuts, cyan = eyes, amber = beak/feet.
    """
    image, draw = layer(size)
    s = size / 240

    def box(x1: int, y1: int, x2: int, y2: int) -> tuple[int, int, int, int]:
        return (round(x1 * s), round(y1 * s), round(x2 * s), round(y2 * s))

    shell = (255, 79, 184, 255)
    soft = (190, 47, 134, 255)
    hot = (255, 209, 236, 255)
    cyan = (103, 232, 249, 255)
    amber = (251, 191, 36, 255)

    # Feet and shadow anchors first, so body particles sit above them.
    draw.ellipse(box(43, 190, 111, 223), fill=amber)
    draw.ellipse(box(129, 190, 197, 223), fill=amber)
    draw.rectangle(box(73, 202, 168, 213), fill=soft)

    # Flippers/wings.
    draw.ellipse(box(24, 86, 84, 193), fill=shell)
    draw.ellipse(box(156, 86, 216, 193), fill=shell)
    draw.polygon([(48, 112), (23, 168), (58, 154)], fill=hot)
    draw.polygon([(192, 112), (217, 168), (182, 154)], fill=hot)

    # Body and head.
    draw.ellipse(box(55, 78, 185, 211), fill=shell)
    draw.ellipse(box(64, 22, 176, 126), fill=shell)

    # Belly/face openings keep the tuxedo shape readable in a particle grid.
    draw.ellipse(box(82, 101, 158, 198), fill=soft)
    draw.ellipse(box(78, 53, 162, 112), fill=hot)
    draw.polygon([(120, 99), (96, 151), (144, 151)], fill=hot)

    # Head contour and ears/top pixels.
    draw.rectangle(box(82, 31, 158, 44), fill=shell)
    draw.rectangle(box(94, 20, 110, 35), fill=shell)
    draw.rectangle(box(130, 20, 146, 35), fill=shell)

    # Eyes, beak, tuxedo chest pixels.
    draw.ellipse(box(88, 66, 106, 84), fill=cyan)
    draw.ellipse(box(134, 66, 152, 84), fill=cyan)
    draw.rectangle(box(93, 70, 101, 78), fill=(5, 8, 14, 255))
    draw.rectangle(box(139, 70, 147, 78), fill=(5, 8, 14, 255))
    draw.polygon([(120, 84), (101, 99), (139, 99)], fill=amber)
    draw.polygon([(120, 101), (106, 113), (134, 113)], fill=amber)
    draw.rectangle(box(114, 140, 126, 167), fill=shell)
    draw.rectangle(box(101, 151, 112, 162), fill=shell)
    draw.rectangle(box(128, 151, 139, 162), fill=shell)

    # Add a hard pixelated edge so the particle extraction feels less blobby.
    alpha = image.getchannel("A")
    edge = alpha.filter(ImageFilter.FIND_EDGES).point(lambda p: 255 if p > 20 else 0)
    edge_rgba = Image.new("RGBA", image.size, (255, 79, 184, 0))
    edge_rgba.putalpha(edge)
    image = Image.alpha_composite(image, edge_rgba)
    return image


def default_points() -> list[tuple[int, int, str]]:
    mask = draw_default_tux_mask().resize((GRID_W, GRID_H), Image.Resampling.LANCZOS)
    points: list[tuple[int, int, str]] = []
    for gy in range(GRID_H):
        for gx in range(GRID_W):
            r, g, b, a = mask.getpixel((gx, gy))
            if a < 42:
                continue
            if g > 180 and b > 180:
                part = "eye"
            elif r > 220 and 120 < g < 220 and b < 90:
                part = "beak"
            elif r > 235 and g > 150 and b > 190:
                part = "hot"
            elif r > 150 and b > 100:
                part = "soft"
            else:
                part = "body"
            points.append((gx, gy, part))
    return points


def points_from_image(path: Path) -> list[tuple[int, int, str]]:
    image = Image.open(path).convert("RGBA")
    alpha = image.getchannel("A")
    gray = ImageOps.grayscale(image)
    mask = Image.new("L", image.size, 0)
    mask.paste(gray, mask=alpha)
    mask = ImageOps.autocontrast(mask).resize((GRID_W, GRID_H), Image.Resampling.LANCZOS)
    points: list[tuple[int, int, str]] = []
    for gy in range(GRID_H):
        for gx in range(GRID_W):
            value = mask.getpixel((gx, gy))
            if value > 44:
                points.append((gx, gy, "hot" if value > 170 else "body"))
    return points


def serpentine(points: list[tuple[int, int, str]]) -> list[tuple[int, int, str]]:
    by_coord = {(gx, gy): part for gx, gy, part in points}
    ordered: list[tuple[int, int, str]] = []
    for gy in range(GRID_H):
        xs = range(GRID_W) if gy % 2 == 0 else range(GRID_W - 1, -1, -1)
        for gx in xs:
            part = by_coord.get((gx, gy))
            if part:
                ordered.append((gx, gy, part))
    return ordered


def dot_xy(gx: int, gy: int) -> tuple[int, int]:
    return MAP_X + gx * CELL, MAP_Y + gy * CELL


def draw_corner(draw: ImageDraw.ImageDraw, x: int, y: int, sx: int, sy: int) -> None:
    draw.line((x, y, x + sx * 14, y), fill=BORDER, width=1)
    draw.line((x, y, x, y + sy * 14), fill=BORDER, width=1)


def draw_base() -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(image)

    draw.rounded_rectangle((8, 8, WIDTH - 9, HEIGHT - 9), radius=0, fill=PANEL, outline="#273348")
    draw.rectangle((15, 15, WIDTH - 16, HEIGHT - 16), outline="#334155")
    draw_corner(draw, 21, 21, 1, 1)
    draw_corner(draw, WIDTH - 22, 21, -1, 1)
    draw_corner(draw, 21, HEIGHT - 22, 1, -1)
    draw_corner(draw, WIDTH - 22, HEIGHT - 22, -1, -1)

    draw.text((24, 27), "VISUAL.MAP", fill=TEXT, font=FONT_12)
    draw.text((212, 30), "300x340", fill=MUTED, font=FONT_8)
    draw.text((250, 30), "1-BIT", fill=BORDER, font=FONT_8)
    draw.line((24, 44, WIDTH - 25, 44), fill="#334155")

    for gx in range(GRID_W + 1):
        x = MAP_X + gx * CELL
        color = GRID_HOT if gx % 8 == 0 else GRID
        draw.line((x, MAP_Y - 4, x, MAP_Y + GRID_H * CELL), fill=color)
    for gy in range(GRID_H + 1):
        y = MAP_Y + gy * CELL
        color = GRID_HOT if gy % 8 == 0 else GRID
        draw.line((MAP_X - 4, y, MAP_X + GRID_W * CELL, y), fill=color)

    draw.text((25, 255), "KERNEL//PULSE", fill=BORDER, font=FONT_9)
    draw.text((181, 255), "MODE: SERPENT", fill=MUTED, font=FONT_9)
    draw.line((24, 276, WIDTH - 25, 276), fill="#334155")
    draw.text((24, 289), "PTS 18000", fill=TEXT, font=FONT_10)
    draw.text((101, 289), "·", fill=BORDER, font=FONT_10)
    draw.text((117, 289), "FS/SERPENTINE", fill=TEXT, font=FONT_10)
    draw.text((24, 307), "SCAN LOOP: ON", fill=MUTED, font=FONT_9)
    draw.text((186, 307), "fguzman-stack", fill=BORDER, font=FONT_9)
    return image


def palette_for(part: str, intensity: float) -> str:
    if part == "eye":
        return CYAN if intensity > 0.5 else "#28606a"
    if part == "beak":
        return AMBER if intensity > 0.5 else "#6a501a"
    if part == "hot":
        return HOT if intensity > 0.72 else "#ff9ad0"
    if part == "soft":
        return "#ff8ac7" if intensity > 0.55 else NEON_SOFT
    return NEON if intensity > 0.5 else NEON_DIM


def draw_frame(base: Image.Image, ordered: list[tuple[int, int, str]], frame: int, total: int) -> Image.Image:
    image = base.copy().convert("RGBA")
    draw = ImageDraw.Draw(image)
    glow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)

    count = len(ordered)
    head = int((frame / total) * count)
    tail = 92
    pulse = (math.sin((frame / total) * math.tau) + 1) / 2

    # Dim full logo is always present; the moving window redraws it hot.
    for index, (gx, gy, part) in enumerate(ordered):
        x, y = dot_xy(gx, gy)
        distance = (head - index) % count
        in_tail = distance < tail
        sparkle = (index * 17 + frame * 11) % 97 == 0
        intensity = 1.0 - (distance / tail) if in_tail else 0.18 + pulse * 0.05
        color = palette_for(part, intensity)
        radius = DOT + (1 if in_tail and distance < 18 else 0)

        if in_tail:
            glow_draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill=(255, 79, 184, 34 + int(50 * intensity)))
        if sparkle:
            draw.line((x - 3, y, x + 3, y), fill=HOT)
            draw.line((x, y - 3, x, y + 3), fill=HOT)
        else:
            draw.rectangle((x - radius, y - radius, x + radius, y + radius), fill=color)

    sx, sy, _ = ordered[head % count]
    scan_x, scan_y = dot_xy(sx, sy)
    draw.rectangle((scan_x - 6, scan_y - 6, scan_x + 6, scan_y + 6), outline=HOT)
    draw.line((MAP_X - 8, scan_y, MAP_X + GRID_W * CELL + 4, scan_y), fill="#3b2942")
    draw.line((scan_x, MAP_Y - 7, scan_x, MAP_Y + GRID_H * CELL + 3), fill="#26364f")

    # Subtle CRT jitter/glitch bars.
    for offset in (0, 41, 83):
        gy = MAP_Y + ((frame * 3 + offset) % (GRID_H * CELL))
        draw.line((25, gy, WIDTH - 26, gy), fill="#111827")

    image = Image.alpha_composite(image, glow.filter(ImageFilter.GaussianBlur(3)))
    return image.convert("P", palette=Image.Palette.ADAPTIVE, colors=96)


def generate(points: list[tuple[int, int, str]], output: Path, frames: int, duration: int) -> None:
    ordered = serpentine(points)
    if not ordered:
        raise SystemExit("No points found. Try a higher-contrast input image.")
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
    parser.add_argument("--frames", type=int, default=96)
    parser.add_argument("--duration", type=int, default=38, help="Frame duration in ms.")
    args = parser.parse_args()

    points = points_from_image(args.input) if args.input else default_points()
    generate(points, args.output, args.frames, args.duration)
    print(f"Generated {args.output} ({len(points)} particles, {args.frames} frames)")


if __name__ == "__main__":
    main()
