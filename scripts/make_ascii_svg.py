#!/usr/bin/env python3
"""Generate an animated terminal-style ASCII portrait from a local image.

The input image is read from the path passed on the command line and is never
copied into the repository. Only the generated SVG should be committed.

Usage: python scripts/make_ascii_svg.py <photo> [output.svg]
"""

from __future__ import annotations

import html
import os
from pathlib import Path
import sys

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps


COLS = 82
ROWS = 38
CELL_W = 7.4
CELL_H = 13.2
RAMP = " .`:-=+*cs#%@"

PAD = 18
TITLEBAR_H = 30
STATUS_H = 34
ART_W = COLS * CELL_W
ART_H = ROWS * CELL_H
CANVAS_W = round(ART_W + PAD * 2)
CANVAS_H = round(TITLEBAR_H + ART_H + STATUS_H + PAD)

BG = "#0d1117"
BG_TOP = "#15102b"
FRAME = "#30363d"
MUTED = "#8b949e"
INK = "#dbe7ff"
CYAN = "#00e5ff"
PURPLE = "#a371f7"

DRAW_START = 0.45
ROW_DUR = 0.18
STAGGER = 0.18
DRAW_TOTAL_SECONDS = DRAW_START + (ROWS - 1) * STAGGER + ROW_DUR


def prepare(source: Path) -> Image.Image:
    image = Image.open(source).convert("RGB")
    width, height = image.size

    # Keep the face and shoulders while removing most of the busy surroundings.
    left = int(width * 0.08)
    right = int(width * 0.92)
    upper = int(height * 0.01)
    lower = int(height * 0.99)
    image = image.crop((left, upper, right, lower))

    gray = ImageOps.grayscale(image)
    gray = ImageOps.autocontrast(gray, cutoff=1)
    gray = ImageEnhance.Contrast(gray).enhance(1.18)
    gray = ImageEnhance.Brightness(gray).enhance(1.28)
    gray = gray.filter(ImageFilter.UnsharpMask(radius=1.2, percent=115, threshold=3))

    # A feathered portrait mask keeps the generated asset recognizable without
    # embedding the source photo or its background pixels in the SVG.
    mask = Image.new("L", gray.size, 0)
    draw = ImageDraw.Draw(mask)
    mw, mh = mask.size
    draw.ellipse((mw * 0.13, -mh * 0.05, mw * 0.87, mh * 0.75), fill=255)
    draw.polygon(
        [
            (mw * 0.17, mh * 0.48),
            (mw * 0.83, mh * 0.48),
            (mw, mh * 0.66),
            (mw, mh),
            (0, mh),
            (0, mh * 0.66),
        ],
        fill=255,
    )
    mask = mask.filter(ImageFilter.GaussianBlur(radius=max(8, mw // 30)))
    gray = Image.composite(gray, Image.new("L", gray.size, 255), mask)

    # Preserve character proportions when sampling the portrait grid.
    target_ratio = (COLS * CELL_W) / (ROWS * CELL_H)
    current_ratio = gray.width / gray.height
    if current_ratio > target_ratio:
        new_width = int(gray.height * target_ratio)
        offset = (gray.width - new_width) // 2
        gray = gray.crop((offset, 0, offset + new_width, gray.height))
    else:
        new_height = int(gray.width / target_ratio)
        offset = max(0, (gray.height - new_height) // 3)
        gray = gray.crop((0, offset, gray.width, min(gray.height, offset + new_height)))

    return gray.resize((COLS, ROWS), Image.Resampling.LANCZOS)


def rows_from_image(image: Image.Image) -> list[str]:
    pixels = image.load()
    rows: list[str] = []
    for y in range(ROWS):
        chars: list[str] = []
        for x in range(COLS):
            luminance = (pixels[x, y] / 255.0) ** 1.28
            if luminance >= 0.84:
                chars.append(" ")
                continue
            index = round((1.0 - luminance) * (len(RAMP) - 1))
            chars.append(RAMP[max(0, min(len(RAMP) - 1, index))])
        rows.append("".join(chars))
    return rows


def render(rows: list[str], static: bool = False) -> str:
    art_top = TITLEBAR_H + 8
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_W}" height="{CANVAS_H}" '
        f'viewBox="0 0 {CANVAS_W} {CANVAS_H}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
        '<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{BG_TOP}"/><stop offset="0.58" stop-color="{BG}"/>'
        f'<stop offset="1" stop-color="#071820"/></linearGradient></defs>',
        f'<rect width="{CANVAS_W}" height="{CANVAS_H}" rx="8" fill="url(#bg)"/>',
        f'<rect x="0.5" y="0.5" width="{CANVAS_W - 1}" height="{CANVAS_H - 1}" rx="8" '
        f'fill="none" stroke="{FRAME}"/>',
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{CANVAS_W}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>',
    ]

    for i, color in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
        parts.append(f'<circle cx="{PAD + i * 16}" cy="15" r="5" fill="{color}"/>')
    parts.append(
        f'<text x="{CANVAS_W / 2}" y="19" fill="{MUTED}" font-size="11" text-anchor="middle">'
        'akshat@github: ~/identity/portrait.sh</text>'
    )

    font_size = CELL_H * 0.86
    for row_index, row in enumerate(rows):
        y = art_top + row_index * CELL_H + CELL_H * 0.76
        row_y = art_top + row_index * CELL_H
        safe = html.escape(row)
        text = (
            f'<text xml:space="preserve" x="{PAD}" y="{y:.1f}" fill="{INK}" '
            f'font-size="{font_size:.1f}" textLength="{ART_W:.1f}" '
            f'lengthAdjust="spacing">{safe}</text>'
        )
        if static:
            parts.append(text)
            continue

        delay = DRAW_START + row_index * STAGGER
        parts.append(
            f'<clipPath id="row-{row_index}"><rect x="{PAD}" y="{row_y:.1f}" height="{CELL_H:.1f}" width="0">'
            f'<animate attributeName="width" from="0" to="{ART_W:.1f}" begin="{delay:.3f}s" '
            f'dur="{ROW_DUR:.2f}s" fill="freeze"/></rect></clipPath>'
        )
        parts.append(f'<g clip-path="url(#row-{row_index})">{text}</g>')
        parts.append(
            f'<rect id="draw-cursor-{row_index}" class="draw-cursor" x="{PAD}" y="{row_y + 1:.1f}" '
            f'width="{CELL_W:.1f}" height="{CELL_H - 2:.1f}" fill="{CYAN}" opacity="0">'
            f'<animate attributeName="x" from="{PAD}" to="{PAD + ART_W:.1f}" begin="{delay:.3f}s" '
            f'dur="{ROW_DUR:.2f}s" fill="freeze"/>'
            f'<set attributeName="opacity" to="0.95" begin="{delay:.3f}s"/>'
            f'<set attributeName="opacity" to="0" begin="{delay + ROW_DUR:.3f}s"/></rect>'
        )

    status_line = TITLEBAR_H + ART_H + 10
    status_y = status_line + 22
    parts.extend(
        [
            f'<line x1="0" y1="{status_line:.1f}" x2="{CANVAS_W}" y2="{status_line:.1f}" stroke="{FRAME}"/>',
            f'<text x="{PAD}" y="{status_y:.1f}" fill="{MUTED}" font-size="12">'
            f'<tspan fill="{CYAN}">akshat</tspan>@github:~$ whoami '
            f'<tspan fill="{PURPLE}" font-weight="700">Akshat Sinha</tspan></text>',
            f'<rect x="{PAD + 259}" y="{status_y - 12:.1f}" width="7" height="14" fill="{CYAN}">'
            '<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.51;1" '
            'dur="1s" repeatCount="indefinite"/></rect>',
            '</svg>',
        ]
    )
    return "".join(parts)


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("usage: make_ascii_svg.py <photo> [output.svg]")
    source = Path(sys.argv[1]).expanduser().resolve()
    output = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("akshat-ascii.svg")
    if not source.is_file():
        raise SystemExit(f"photo not found: {source}")
    output.write_text(render(rows_from_image(prepare(source)), bool(os.environ.get("STATIC"))), encoding="utf-8")
    print(f"wrote {output} ({CANVAS_W}x{CANVAS_H}); source remained at {source}")


if __name__ == "__main__":
    main()
