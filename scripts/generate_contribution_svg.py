#!/usr/bin/env python3
"""Fetch public contribution data and render an animated profile SVG."""

from __future__ import annotations

import datetime as dt
import html
import json
from pathlib import Path
import sys
from urllib.request import Request, urlopen


USER = sys.argv[1] if len(sys.argv) > 1 else "akshatsinha0"
OUTPUT = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("contribution-grid.svg")
API = f"https://github-contributions-api.jogruber.de/v4/{USER}?y=last"

CELL = 12
GAP = 3
STEP = CELL + GAP
LEFT = 48
TOP = 58
BOTTOM = 60
COLORS = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
MUTED = "#8b949e"
TEXT = "#e6edf3"
CYAN = "#00e5ff"
PURPLE = "#a371f7"


def fetch() -> dict:
    request = Request(API, headers={"User-Agent": "akshatsinha0-profile-readme/1.0"})
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def streaks(contributions: list[dict]) -> tuple[int, int]:
    runs: list[int] = []
    current = 0
    for day in contributions:
        if day["count"] > 0:
            current += 1
        else:
            runs.append(current)
            current = 0
    runs.append(current)

    index = len(contributions) - 1
    if index >= 0 and contributions[index]["count"] == 0:
        index -= 1
    active = 0
    while index >= 0 and contributions[index]["count"] > 0:
        active += 1
        index -= 1
    return active, max(runs, default=0)


def render(data: dict) -> str:
    days = data["contributions"]
    weeks = (len(days) + 6) // 7
    width = LEFT + weeks * STEP + 24
    height = TOP + 7 * STEP + BOTTOM
    total = data["total"]["lastYear"]
    current, longest = streaks(days)
    best = max(days, key=lambda day: day["count"])

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
        '<style>.cell{opacity:0;animation:reveal .42s cubic-bezier(.2,.8,.2,1) both}'
        '@keyframes reveal{0%{opacity:0;transform:translateY(-6px)}100%{opacity:1;transform:translateY(0)}}'
        '@media(prefers-reduced-motion:reduce){.cell{opacity:1;animation:none}}</style>',
        '<defs><linearGradient id="heat-bg" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0" stop-color="#111827"/><stop offset="0.55" stop-color="#0d1117"/>'
        '<stop offset="1" stop-color="#120d22"/></linearGradient></defs>',
        f'<rect width="{width}" height="{height}" rx="8" fill="url(#heat-bg)"/>',
        f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="8" fill="none" stroke="#30363d"/>',
        '<circle cx="20" cy="15" r="5" fill="#ff5f56"/><circle cx="36" cy="15" r="5" fill="#ffbd2e"/>'
        '<circle cx="52" cy="15" r="5" fill="#27c93f"/>',
        f'<text x="{width / 2}" y="19" fill="{MUTED}" font-size="11" text-anchor="middle">'
        'akshat@github: ~/activity $ ./contributions.sh</text>',
        '<line x1="0" y1="30" x2="100%" y2="30" stroke="#30363d"/>',
    ]

    first_date = dt.date.fromisoformat(days[0]["date"])
    seen_months: set[tuple[int, int]] = set()
    for week in range(weeks):
        day_index = week * 7
        if day_index >= len(days):
            break
        date = dt.date.fromisoformat(days[day_index]["date"])
        key = (date.year, date.month)
        if key not in seen_months and date.day <= 7:
            seen_months.add(key)
            parts.append(
                f'<text x="{LEFT + week * STEP}" y="48" fill="{MUTED}" font-size="10">{date.strftime("%b")}</text>'
            )

    for label, row in (("Mon", 1), ("Wed", 3), ("Fri", 5)):
        y = TOP + row * STEP + CELL * 0.78
        parts.append(f'<text x="16" y="{y:.1f}" fill="{MUTED}" font-size="9">{label}</text>')

    for index, day in enumerate(days):
        week, row = divmod(index, 7)
        x = LEFT + week * STEP
        y = TOP + row * STEP
        level = max(0, min(4, int(day["level"])))
        delay = week * 0.018 + row * 0.04
        title = html.escape(f'{day["date"]}: {day["count"]} contributions')
        parts.append(
            f'<rect class="cell" x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" '
            f'fill="{COLORS[level]}" style="animation-delay:{delay:.3f}s"><title>{title}</title></rect>'
        )

    footer_y = TOP + 7 * STEP + 28
    parts.extend(
        [
            f'<line x1="16" y1="{footer_y - 17}" x2="{width - 16}" y2="{footer_y - 17}" stroke="#30363d"/>',
            f'<text x="20" y="{footer_y}" fill="{TEXT}" font-size="12">'
            f'<tspan fill="{CYAN}" font-weight="700">{total:,}</tspan> contributions in the last year</text>',
            f'<text x="{width / 2}" y="{footer_y}" fill="{MUTED}" font-size="12" text-anchor="middle">'
            f'current <tspan fill="{PURPLE}" font-weight="700">{current}d</tspan>  |  longest '
            f'<tspan fill="{PURPLE}" font-weight="700">{longest}d</tspan></text>',
            f'<text x="{width - 20}" y="{footer_y}" fill="{MUTED}" font-size="12" text-anchor="end">best '
            f'<tspan fill="#f2cc60" font-weight="700">{best["count"]}</tspan> on {best["date"]}</text>',
            '</svg>',
        ]
    )
    return "".join(parts)


if __name__ == "__main__":
    payload = fetch()
    OUTPUT.write_text(render(payload), encoding="utf-8")
    print(f"wrote {OUTPUT} for {USER}")
