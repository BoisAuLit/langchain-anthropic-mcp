#!/usr/bin/env python3
"""Apply cool-tone dark palette to .ipynb files.

Replaces light-theme color blocks with dark-mode equivalents.
Each colored div gets a class + scoped <style> so bold (<strong>) shows in a
distinct accent color per box type.
"""

import json
import re
import sys
from pathlib import Path

DIR = Path(__file__).parent

# bg_hex -> (new_bg, body_color, border_color, class_name, strong_color)
# Strong color chosen for cross-hue contrast (warm vs cool) — not just brightness shift.
BOX_PALETTE = {
    "#e8f4fd": ("#1e293b", "#e2e8f0", "#60a5fa", "dark-info",    "#fbbf24"),  # amber on off-white
    "#fff3b0": ("#2a2418", "#fde68a", "#fbbf24", "dark-warning", "#f9a8d4"),  # pink on yellow
    "#ffe6e6": ("#2d1f1f", "#fca5a5", "#f87171", "dark-error",   "#fde047"),  # yellow on red
    "#e7f7e9": ("#1a2e1f", "#bbf7d0", "#4ade80", "dark-success", "#fbbf24"),  # amber on green
    "#f0f9ff": ("#0f2729", "#a5f3fc", "#22d3ee", "dark-cyan",    "#fbbf24"),  # amber on cyan
    "#fff8e1": ("#2d2418", "#fed7aa", "#fb923c", "dark-orange",  "#67e8f9"),  # cyan on orange
}

GRADIENT_MAP = {
    "linear-gradient(90deg,#0366d6,#6f42c1)": "linear-gradient(90deg,#1e3a8a,#5b21b6)",
    "linear-gradient(90deg,#0366d6,#28a745)": "linear-gradient(90deg,#1e3a8a,#15803d)",
    "linear-gradient(90deg,#6f42c1,#0366d6)": "linear-gradient(90deg,#5b21b6,#1e3a8a)",
    "linear-gradient(90deg,#f4a460,#fd7e14)": "linear-gradient(90deg,#9a3412,#7c2d12)",
    "linear-gradient(90deg,#dc3545,#fd7e14,#28a745)": "linear-gradient(90deg,#991b1b,#9a3412,#15803d)",
    "linear-gradient(90deg,#28a745,#6f42c1)": "linear-gradient(90deg,#15803d,#5b21b6)",
    "linear-gradient(90deg,#28a745,#1abc9c)": "linear-gradient(90deg,#15803d,#0e7490)",
    "linear-gradient(90deg,#0366d6,#1abc9c)": "linear-gradient(90deg,#1e3a8a,#0e7490)",
}

CODE_BG = ("#f6f8fa", "#1e1e2e", "#d4d4d4")
HIGHLIGHT_BG = ("#fff3a3", "#3d3414", "#fde047")


# Lenient quote: matches " or \"  (some cells have backslash-escaped quotes in markdown source)
Q = r'(\\?")'


def upgrade_box(text):
    """Replace each colored div with dark + class + scoped <style>."""
    for old_bg, (new_bg, body, border, cls, strong) in BOX_PALETTE.items():
        pattern = re.compile(
            r'<div style=' + Q + r'background:' + re.escape(old_bg)
            + r';\s*padding:(\d+px \d+px);'
            + r'\s*border-left:4px solid #[0-9a-fA-F]+;'
            + r'\s*border-radius:4px;'
            + r'(?:\s*margin:[^;]+;)?'                # optional margin
            + r'\s*width:\s*97%;?\s*\1>',             # tolerate `width: 97%` no trailing `;`
            re.DOTALL,
        )

        def repl(m, _new_bg=new_bg, _body=body, _border=border, _cls=cls, _strong=strong):
            q = m.group(1)
            padding = m.group(2)
            return (
                f'<div class={q}{_cls}{q} '
                f'style={q}background:{_new_bg}; color:{_body}; padding:{padding}; '
                f'border-left:4px solid {_border}; border-radius:4px; width:97%;{q}>'
                f'<style>.{_cls} strong{{color:{_strong};}}</style>'
            )

        text = pattern.sub(repl, text)
    return text


def upgrade_gradient_title(text):
    """Replace gradient title divs. Add class + bold accent."""
    for old, new in GRADIENT_MAP.items():
        text = text.replace(f"background:{old}", f"background:{new}")
    pattern = re.compile(
        r'<div style=' + Q + r'background:(linear-gradient\([^)]+\));'
        + r'\s*color:white;\s*padding:20px 32px;\s*border-radius:8px;'
        + r'\s*width:\s*97%;?\s*\1>',
        re.DOTALL,
    )

    def repl(m):
        q = m.group(1)
        grad = m.group(2)
        return (
            f'<div class={q}dark-title{q} '
            f'style={q}background:{grad}; color:#f1f5f9; padding:20px 32px; '
            f'border-radius:8px; width:97%;{q}>'
            f'<style>.dark-title strong{{color:#fde047;}}</style>'
        )

    text = pattern.sub(repl, text)
    return text


def upgrade_code_block(text):
    """<pre style="background:#f6f8fa; ...">"""
    old_bg, new_bg, body = CODE_BG
    pattern = re.compile(
        r'<pre style=' + Q + r'background:' + re.escape(old_bg)
        + r';\s*padding:(\d+px \d+px);'
        + r'\s*border-radius:4px;'
        + r'\s*font-size:([\d.]+em);'                 # accept any font-size
        + r'\s*width:\s*97%;?\s*\1>',
        re.DOTALL,
    )

    def repl(m):
        q = m.group(1)
        padding = m.group(2)
        fs = m.group(3)
        return (
            f'<pre style={q}background:{new_bg}; color:{body}; padding:{padding}; '
            f'border-radius:4px; font-size:{fs}; width:97%;{q}>'
        )

    text = pattern.sub(repl, text)
    return text


def upgrade_highlight_span(text):
    """<span style="background:#fff3a3; padding:0 2px;">"""
    old_bg, new_bg, body = HIGHLIGHT_BG
    pattern = re.compile(
        r'<span style=' + Q + r'background:' + re.escape(old_bg)
        + r';\s*padding:0 2px;\s*\1>',
        re.DOTALL,
    )

    def repl(m):
        q = m.group(1)
        return f'<span style={q}background:{new_bg}; color:{body}; padding:0 2px;{q}>'

    text = pattern.sub(repl, text)
    return text


def process_text(text):
    text = upgrade_box(text)
    text = upgrade_gradient_title(text)
    text = upgrade_code_block(text)
    text = upgrade_highlight_span(text)
    return text


def process_notebook(path):
    with open(path, "r", encoding="utf-8") as f:
        nb = json.load(f)
    changed = 0
    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "markdown":
            continue
        src = cell.get("source", [])
        if isinstance(src, list):
            text = "".join(src)
        else:
            text = src
        new_text = process_text(text)
        if new_text != text:
            changed += 1
            if isinstance(src, list):
                # Preserve line-per-element format. Split on \n but keep them as line endings.
                lines = new_text.splitlines(keepends=True)
                cell["source"] = lines
            else:
                cell["source"] = new_text
    with open(path, "w", encoding="utf-8") as f:
        json.dump(nb, f, ensure_ascii=False, indent=1)
    return changed


def main():
    files = sys.argv[1:] if len(sys.argv) > 1 else sorted(p.name for p in DIR.glob("*.ipynb"))
    for name in files:
        p = DIR / name
        if not p.exists():
            print(f"  SKIP (not found): {name}")
            continue
        n = process_notebook(p)
        print(f"  {name}: {n} markdown cell(s) updated")


if __name__ == "__main__":
    main()
