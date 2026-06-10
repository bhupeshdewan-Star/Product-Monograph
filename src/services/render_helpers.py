from __future__ import annotations

from html import escape
from typing import Iterable


def split_blocks(text: str) -> list[str]:
    return [block.strip() for block in (text or "").split("\n\n") if block.strip()]


def is_markdown_table(block: str) -> bool:
    lines = [line.strip() for line in block.splitlines() if line.strip()]
    if len(lines) < 2 or "|" not in lines[0] or "|" not in lines[1]:
        return False
    separator = lines[1].replace("|", "").replace(":", "").replace("-", "").strip()
    return separator == ""


def parse_markdown_table(block: str) -> list[list[str]]:
    lines = [line.strip() for line in block.splitlines() if line.strip()]
    if len(lines) < 2:
        return []
    rows: list[list[str]] = []
    for index, line in enumerate(lines):
        if index == 1:
            continue
        if "|" not in line:
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        rows.append(cells)
    return rows


def is_bullet_block(block: str) -> bool:
    lines = [line.strip() for line in block.splitlines() if line.strip()]
    return bool(lines) and all(line.startswith("- ") for line in lines)


def normalize_unicode_text(text: str) -> str:
    return text or ""


def placeholder_items(placeholders: dict | None) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    if not placeholders:
        return items
    for bucket, entries in placeholders.items():
        for entry in entries or []:
            items.append(
                {
                    "bucket": bucket,
                    "label": entry.get("label", "Placeholder"),
                    "status": entry.get("status", "draft placeholder"),
                    "instruction": entry.get("instruction", ""),
                }
            )
    return items


def html_table(rows: Iterable[Iterable[str]], header: bool = True) -> str:
    rows = [list(row) for row in rows]
    if not rows:
        return "<table class='mono-table'></table>"
    parts = ["<table class='mono-table'>"]
    for idx, row in enumerate(rows):
        cells = "".join(
            f"<th>{escape(str(cell))}</th>" if header and idx == 0 else f"<td>{escape(str(cell))}</td>"
            for cell in row
        )
        parts.append(f"<thead><tr>{cells}</tr></thead>" if header and idx == 0 else f"<tr>{cells}</tr>")
    parts.append("</table>")
    return "".join(parts)


def placeholder_callout_html(item: dict[str, str]) -> str:
    return (
        "<div class='placeholder-box'>"
        f"<div class='placeholder-label'>{escape(item.get('label', 'Placeholder'))}</div>"
        f"<div class='placeholder-status'>{escape(item.get('status', 'draft placeholder'))}</div>"
        f"<div class='placeholder-instruction'>{escape(item.get('instruction', ''))}</div>"
        "</div>"
    )
