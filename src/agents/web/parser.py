from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup


def _text(node) -> str:
    return re.sub(r"\s+", " ", node.get_text(" ", strip=True)) if node else ""


def _style_map(style: str) -> dict:
    result = {}
    for chunk in (style or "").split(";"):
        if ":" not in chunk:
            continue
        key, value = chunk.split(":", 1)
        result[key.strip().lower()] = value.strip().lower()
    return result


def _parse_color(value: str) -> Optional[tuple[int, int, int]]:
    if not value:
        return None
    value = value.strip().lower()
    if value.startswith("#"):
        hex_value = value[1:]
        if len(hex_value) == 3:
            hex_value = "".join(ch * 2 for ch in hex_value)
        if len(hex_value) == 6:
            try:
                return tuple(int(hex_value[i : i + 2], 16) for i in (0, 2, 4))
            except ValueError:
                return None
    rgb = re.match(r"rgba?\((\d+),\s*(\d+),\s*(\d+)", value)
    if rgb:
        return tuple(int(rgb.group(i)) for i in (1, 2, 3))
    return None


def _relative_luminance(rgb: tuple[int, int, int]) -> float:
    def channel(c: int) -> float:
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = rgb
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def _contrast_ratio(fg: tuple[int, int, int], bg: tuple[int, int, int]) -> float:
    l1 = _relative_luminance(fg)
    l2 = _relative_luminance(bg)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def parse_page_snapshot(html: str, base_url: str = "") -> Dict[str, Any]:
    soup = BeautifulSoup(html or "", "html.parser")

    headings = []
    heading_counter = Counter()
    for tag_name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
        for tag in soup.find_all(tag_name):
            heading_counter[tag_name] += 1
            headings.append({
                "tag": tag_name,
                "level": int(tag_name[1]),
                "text": _text(tag),
            })

    images = []
    for img in soup.find_all("img"):
        images.append({
            "src": urljoin(base_url, img.get("src", "")),
            "alt": img.get("alt"),
            "has_alt": img.has_attr("alt") and bool(str(img.get("alt", "")).strip()),
            "aria_label": img.get("aria-label"),
            "title": img.get("title"),
        })

    links = []
    for link in soup.find_all("a"):
        links.append({
            "href": urljoin(base_url, link.get("href", "")) if link.get("href") else "",
            "text": _text(link),
            "has_text": bool(_text(link)),
            "aria_label": link.get("aria-label"),
            "role": link.get("role"),
            "tabindex": link.get("tabindex"),
        })

    buttons = []
    for button in soup.find_all(["button", "input"]):
        if button.name == "input" and button.get("type", "").lower() not in {"button", "submit", "reset"}:
            continue
        buttons.append({
            "tag": button.name,
            "type": button.get("type"),
            "text": _text(button) if button.name == "button" else button.get("value", ""),
            "aria_label": button.get("aria-label"),
            "title": button.get("title"),
            "role": button.get("role"),
            "tabindex": button.get("tabindex"),
        })

    inputs = []
    labels_by_for = {
        lab.get("for"): _text(lab) for lab in soup.find_all("label") if lab.get("for")
    }
    for field in soup.find_all(["input", "textarea", "select"]):
        field_id = field.get("id") or ""
        associated_label = ""
        if field_id and field_id in labels_by_for:
            associated_label = labels_by_for[field_id]
        parent_label = field.find_parent("label")
        if parent_label and not associated_label:
            associated_label = _text(parent_label)
        inputs.append({
            "tag": field.name,
            "type": field.get("type", field.name),
            "id": field_id,
            "name": field.get("name"),
            "placeholder": field.get("placeholder"),
            "required": field.has_attr("required"),
            "aria_label": field.get("aria-label"),
            "aria_labelledby": field.get("aria-labelledby"),
            "label_text": associated_label,
            "autocomplete": field.get("autocomplete"),
            "tabindex": field.get("tabindex"),
        })

    forms = []
    for form in soup.find_all("form"):
        form_inputs = form.find_all(["input", "textarea", "select"])
        labelled = 0
        for field in form_inputs:
            field_id = field.get("id") or ""
            if field_id and field_id in labels_by_for:
                labelled += 1
            elif field.find_parent("label"):
                labelled += 1
            elif field.get("aria-label") or field.get("aria-labelledby"):
                labelled += 1
        forms.append({
            "action": urljoin(base_url, form.get("action", "")) if form.get("action") else "",
            "method": form.get("method", "get"),
            "field_count": len(form_inputs),
            "labelled_field_count": labelled,
        })

    meta_viewport = soup.find("meta", attrs={"name": re.compile("^viewport$", re.I)})
    meta_description = soup.find("meta", attrs={"name": re.compile("^description$", re.I)})
    lang = soup.find("html").get("lang") if soup.find("html") else None

    semantic_tags = {
        tag: len(soup.find_all(tag))
        for tag in ["main", "nav", "header", "footer", "article", "section", "aside"]
    }

    inline_contrast_samples = []
    for node in soup.find_all(True):
        style = _style_map(node.get("style", ""))
        fg = _parse_color(style.get("color", ""))
        bg = _parse_color(style.get("background-color", style.get("background", "")))
        if fg and bg:
            ratio = _contrast_ratio(fg, bg)
            inline_contrast_samples.append(
                {
                    "tag": node.name,
                    "text": _text(node)[:80],
                    "ratio": round(ratio, 2),
                    "passes_wcag_aa": ratio >= 4.5,
                }
            )

    text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True))
    text_excerpt = text[:3000]

    aria_attrs = []
    duplicate_ids = []
    ids = []
    for node in soup.find_all(True):
        node_id = node.get("id")
        if node_id:
            ids.append(node_id)
        attrs = {k: v for k, v in node.attrs.items() if str(k).lower().startswith("aria-")}
        if attrs:
            aria_attrs.append(
                {
                    "tag": node.name,
                    "role": node.get("role"),
                    "attrs": attrs,
                    "text": _text(node)[:80],
                }
            )
    seen_ids = set()
    for item in ids:
        if item in seen_ids and item not in duplicate_ids:
            duplicate_ids.append(item)
        seen_ids.add(item)

    return {
        "title": _text(soup.find("title")) if soup.find("title") else "",
        "lang": lang,
        "meta_description": meta_description.get("content") if meta_description else "",
        "meta_viewport": meta_viewport.get("content") if meta_viewport else "",
        "headings": headings,
        "heading_counts": dict(heading_counter),
        "images": images,
        "links": links,
        "buttons": buttons,
        "inputs": inputs,
        "forms": forms,
        "semantic_tags": semantic_tags,
        "aria_usage": aria_attrs,
        "duplicate_ids": duplicate_ids,
        "inline_contrast_samples": inline_contrast_samples,
        "text_excerpt": text_excerpt,
        "text_length": len(text),
    }


def parse_checklist_document(html: str, base_url: str = "") -> Dict[str, Any]:
    soup = BeautifulSoup(html or "", "html.parser")
    main = soup.find("main") or soup.find("article") or soup.body or soup

    sections: List[Dict[str, Any]] = []
    current_section = {"title": "", "items": []}

    for node in main.find_all(["h1", "h2", "h3", "h4", "li", "p"], recursive=True):
        if node.name in {"h1", "h2", "h3", "h4"}:
            if current_section["title"] or current_section["items"]:
                sections.append(current_section)
            current_section = {"title": _text(node), "items": []}
        elif node.name == "li":
            current_section["items"].append(_text(node))
        elif node.name == "p":
            text = _text(node)
            if text and len(text) > 20 and len(current_section["items"]) < 2:
                current_section["items"].append(text)

    if current_section["title"] or current_section["items"]:
        sections.append(current_section)

    all_items = []
    for section in sections:
        for item in section["items"]:
            all_items.append({"section": section["title"], "text": item})

    return {
        "title": _text(soup.find("title")) if soup.find("title") else "",
        "h1": _text(soup.find("h1")) if soup.find("h1") else "",
        "sections": sections,
        "items": all_items,
        "source_text": re.sub(r"\s+", " ", main.get_text(" ", strip=True))[:8000],
    }

