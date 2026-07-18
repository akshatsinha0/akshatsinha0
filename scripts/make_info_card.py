#!/usr/bin/env python3
"""Generate the terminal identity card embedded in the profile README."""

from __future__ import annotations

import html
import os
from pathlib import Path


WIDTH = 520
HEIGHT = 412
PAD = 20
TITLEBAR_H = 30
LINE_H = 21

BG = "#0d1117"
BG_TOP = "#111827"
FRAME = "#30363d"
TEXT = "#e6edf3"
MUTED = "#8b949e"
CYAN = "#00e5ff"
PURPLE = "#a371f7"
GREEN = "#3fb950"
AMBER = "#f2cc60"

ROWS = [
    ("host",),
    ("kv", "Signal", "Serif for building....."),
    ("gap",),
    ("section", "Systems"),
    ("kv", "Data", "Manufacturing / Migration / Mining"),
    ("kv", "Cloud", "Warm instrumentation / Cloud Fabric"),
    ("kv", "Platform", "Staff Architecture-cum-Platform"),
    ("kv", "Frontier", "Edge AI/LLMs / 6G Tower Area N/W"),
    ("gap",),
    ("section", "Stack"),
    ("kv", "Core", "C++ / C / Python / Java"),
    ("kv", "Web", "JavaScript / React / Node.js / Express"),
    ("kv", "Data", "MySQL / MongoDB / AWS"),
    ("kv", "Ops", "Docker / Kubernetes / Terraform"),
    ("gap",),
    ("section", "Builds"),
    ("bullet", "Chess Cheat Detection Engine"),
    ("bullet", "Takes Takes Takes - Chess Game Website"),
    ("bullet", "HereIAm - Real-Time Chat Application"),
]


def rise(content: str, index: int, static: bool) -> str:
    if static:
        return f"<g>{content}</g>"
    delay = 0.10 + index * 0.055
    return (
        f'<g opacity="0" transform="translate(0,5)">{content}'
        f'<animate attributeName="opacity" from="0" to="1" begin="{delay:.2f}s" dur="0.35s" fill="freeze"/>'
        f'<animateTransform attributeName="transform" type="translate" from="0 5" to="0 0" '
        f'begin="{delay:.2f}s" dur="0.35s" fill="freeze"/></g>'
    )


def render(static: bool = False) -> str:
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" '
        'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
        '<defs><linearGradient id="card-bg" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{BG_TOP}"/><stop offset="0.62" stop-color="{BG}"/>'
        '<stop offset="1" stop-color="#120d22"/></linearGradient></defs>',
        f'<rect width="{WIDTH}" height="{HEIGHT}" rx="8" fill="url(#card-bg)"/>',
        f'<rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{HEIGHT - 1}" rx="8" fill="none" stroke="{FRAME}"/>',
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{WIDTH}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>',
    ]
    for i, color in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
        parts.append(f'<circle cx="{PAD + i * 16}" cy="15" r="5" fill="{color}"/>')
    parts.append(
        f'<text x="{WIDTH / 2}" y="19" fill="{MUTED}" font-size="11" text-anchor="middle">'
        'akshat@github: ~$ neofetch --profile</text>'
    )

    y = TITLEBAR_H + 28
    for index, row in enumerate(ROWS):
        kind = row[0]
        if kind == "gap":
            y += LINE_H * 0.48
            continue
        if kind == "host":
            content = (
                f'<text x="{PAD}" y="{y:.1f}" font-size="14" font-weight="700">'
                f'<tspan fill="{CYAN}">akshat</tspan><tspan fill="{MUTED}">@</tspan>'
                f'<tspan fill="{PURPLE}">github</tspan></text>'
                f'<line x1="132" y1="{y - 4:.1f}" x2="{WIDTH - PAD}" y2="{y - 4:.1f}" stroke="{FRAME}"/>'
            )
        elif kind == "section":
            label = html.escape(row[1])
            content = (
                f'<text x="{PAD}" y="{y:.1f}" fill="{CYAN}" font-size="12" font-weight="700">'
                f'&#8212; {label}</text><line x1="{PAD + 32 + len(label) * 8}" y1="{y - 4:.1f}" '
                f'x2="{WIDTH - PAD}" y2="{y - 4:.1f}" stroke="{FRAME}"/>'
            )
        elif kind == "kv":
            content = (
                f'<text x="{PAD}" y="{y:.1f}" fill="{AMBER}" font-size="12" font-weight="700">'
                f'{html.escape(row[1])}</text><text x="118" y="{y:.1f}" fill="{TEXT}" font-size="12">'
                f'{html.escape(row[2])}</text>'
            )
        else:
            content = (
                f'<circle cx="{PAD + 3}" cy="{y - 4:.1f}" r="2.5" fill="{GREEN}"/>'
                f'<text x="{PAD + 14}" y="{y:.1f}" fill="{TEXT}" font-size="12">{html.escape(row[1])}</text>'
            )
        parts.append(rise(content, index, static))
        y += LINE_H

    parts.append('</svg>')
    return "".join(parts)


if __name__ == "__main__":
    output = Path(__file__).resolve().parent.parent / "identity-card.svg"
    output.write_text(render(bool(os.environ.get("STATIC"))), encoding="utf-8")
    print(f"wrote {output} ({WIDTH}x{HEIGHT})")
