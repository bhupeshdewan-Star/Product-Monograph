from __future__ import annotations

import re
from typing import Any, Dict, List

from ..utils import count_by_severity, score_from_issues


def _issue(
    issue_id: str,
    title: str,
    severity: str,
    category: str,
    description: str,
    impact: str,
    evidence: List[str],
    recommended_fixes: List[str],
    wcag_references: List[str],
    target: str | None = None,
) -> Dict[str, Any]:
    return {
        "id": issue_id,
        "title": title,
        "severity": severity,
        "category": category,
        "description": description,
        "impact": impact,
        "evidence": evidence,
        "recommended_fixes": recommended_fixes,
        "wcag_references": wcag_references,
        "target": target,
    }


def evaluate_accessibility(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    issues: List[Dict[str, Any]] = []
    headings = snapshot.get("headings", [])
    images = snapshot.get("images", [])
    forms = snapshot.get("forms", [])
    inputs = snapshot.get("inputs", [])
    buttons = snapshot.get("buttons", [])
    links = snapshot.get("links", [])
    lang = snapshot.get("lang") or ""
    viewport = snapshot.get("meta_viewport") or ""
    semantic_tags = snapshot.get("semantic_tags", {})
    contrast_samples = snapshot.get("inline_contrast_samples", [])

    if not lang:
        issues.append(
            _issue(
                "a11y-lang-1",
                "Document language is missing",
                "medium",
                "semantic-html",
                "The page does not declare a primary language on the html element.",
                "Screen readers may use the wrong pronunciation and language rules.",
                ["html[lang] is missing"],
                ["Set a valid lang attribute on the html element, for example <html lang='en'>."],
                ["3.1.1"],
                "html",
            )
        )

    if not viewport:
        issues.append(
            _issue(
                "a11y-mobile-1",
                "Viewport meta tag is missing",
                "medium",
                "mobile-accessibility",
                "No responsive viewport meta tag was detected.",
                "Mobile zoom and scaling can become unreliable on small screens.",
                ["Missing <meta name='viewport'>"],
                ["Add a responsive viewport meta tag so the page scales correctly on mobile devices."],
                ["1.4.10", "1.4.4"],
                "head",
            )
        )

    if not headings:
        issues.append(
            _issue(
                "a11y-heading-1",
                "No heading structure detected",
                "high",
                "semantic-html",
                "The page does not expose any headings.",
                "Users cannot quickly understand page structure or navigate by headings.",
                ["No h1-h6 elements were found"],
                ["Add a clear h1 and use headings in a logical hierarchy."],
                ["1.3.1", "2.4.6"],
                "document",
            )
        )
    else:
        levels = [item["level"] for item in headings]
        if levels[0] != 1:
            issues.append(
                _issue(
                    "a11y-heading-2",
                    "Heading hierarchy starts below h1",
                    "medium",
                    "semantic-html",
                    "The first heading is not an h1.",
                    "Navigation and outline structure become harder to interpret.",
                    [f"First heading tag: h{levels[0]}"],
                    ["Start the page with exactly one clear h1 heading."],
                    ["1.3.1", "2.4.6"],
                    "headings",
                )
            )
        for prev, curr in zip(levels, levels[1:]):
            if curr - prev > 1:
                issues.append(
                    _issue(
                        "a11y-heading-3",
                        "Heading levels skip a structural level",
                        "low",
                        "semantic-html",
                        "The heading order jumps more than one level.",
                        "This can confuse assistive technology users about the content hierarchy.",
                        [f"Heading levels observed: {levels}"],
                        ["Use heading levels in order without skipping structural levels."],
                        ["1.3.1", "2.4.6"],
                        "headings",
                    )
                )
                break

    missing_alt = [img for img in images if not img.get("has_alt")]
    if missing_alt:
        issues.append(
            _issue(
                "a11y-img-1",
                "Images are missing alt text",
                "high",
                "non-text-content",
                "One or more images do not have meaningful alt text.",
                "Screen reader users may miss essential visual information.",
                [img.get("src", "") for img in missing_alt[:5]],
                [
                    "Add concise alt text for informative images.",
                    "Use empty alt text only for purely decorative images.",
                ],
                ["1.1.1"],
                "images",
            )
        )

    unlabeled_fields = [
        field
        for field in inputs
        if not (field.get("label_text") or field.get("aria_label") or field.get("aria_labelledby"))
    ]
    if unlabeled_fields:
        issues.append(
            _issue(
                "a11y-form-1",
                "Form controls are missing labels",
                "critical",
                "forms",
                "Some inputs, textareas, or selects do not have an associated label.",
                "Users may not understand what data is required or how to complete the form.",
                [f"{field.get('tag')}#{field.get('id') or field.get('name') or 'unnamed'}" for field in unlabeled_fields[:5]],
                [
                    "Associate each control with a visible <label>.",
                    "Use aria-label or aria-labelledby only when a visible label is not practical.",
                ],
                ["1.3.1", "3.3.2", "4.1.2"],
                "forms",
            )
        )

    if forms and any(form.get("field_count", 0) > 0 and form.get("labelled_field_count", 0) == 0 for form in forms):
        issues.append(
            _issue(
                "a11y-form-2",
                "Entire form appears unlabeled",
                "high",
                "forms",
                "One or more forms have inputs but no detectable labels.",
                "Users relying on assistive tech will struggle to submit the form correctly.",
                [f"form action={form.get('action') or 'inline'}" for form in forms if form.get("field_count", 0) > 0],
                ["Ensure each form control is labeled and instructions are programmatically associated."],
                ["1.3.1", "3.3.2"],
                "forms",
            )
        )

    if any(not btn.get("text") and not btn.get("aria_label") for btn in buttons):
        issues.append(
            _issue(
                "a11y-action-1",
                "Buttons lack accessible names",
                "high",
                "interactive-controls",
                "A button or button-like control does not expose an accessible name.",
                "Assistive technologies cannot identify the control's purpose.",
                ["Unnamed button element detected"],
                ["Add visible text, aria-label, or aria-labelledby to every interactive control."],
                ["4.1.2", "2.4.4"],
                "buttons",
            )
        )

    if any(not link.get("has_text") and not link.get("aria_label") for link in links):
        issues.append(
            _issue(
                "a11y-link-1",
                "Links are missing descriptive text",
                "medium",
                "interactive-controls",
                "One or more anchor tags have no visible text or accessible name.",
                "The destination and purpose of the link are unclear.",
                ["Unnamed anchor element detected"],
                ["Give links meaningful text or an accessible label that describes the destination."],
                ["2.4.4", "4.1.2"],
                "links",
            )
        )

    if any(sample.get("ratio", 21.0) < 4.5 for sample in contrast_samples):
        failing = [sample for sample in contrast_samples if sample.get("ratio", 21.0) < 4.5]
        issues.append(
            _issue(
                "a11y-contrast-1",
                "Inline color contrast fails WCAG AA",
                "high",
                "color-contrast",
                "At least one inline style combination appears to have insufficient text contrast.",
                "Users with low vision may not be able to read the content reliably.",
                [f"{sample.get('tag')}: ratio {sample.get('ratio')}" for sample in failing[:5]],
                [
                    "Increase foreground/background contrast to at least 4.5:1 for body text.",
                    "Use 3:1 only for large text and UI components where appropriate.",
                ],
                ["1.4.3", "1.4.11"],
                "styles",
            )
        )

    if any(field.get("tabindex") and str(field.get("tabindex")).startswith("-") is False and int(str(field.get("tabindex"))) > 0 for field in inputs if str(field.get("tabindex") or "").lstrip("-").isdigit()):
        issues.append(
            _issue(
                "a11y-keyboard-1",
                "Positive tabindex values were detected",
                "medium",
                "keyboard-navigation",
                "Interactive controls use a positive tabindex.",
                "This can create a confusing keyboard navigation order.",
                ["tabindex > 0 found on at least one control"],
                ["Remove positive tabindex values and rely on the natural DOM order."],
                ["2.4.3"],
                "interactive-elements",
            )
        )

    if any(link.get("role") == "button" and not link.get("tabindex") for link in links):
        issues.append(
            _issue(
                "a11y-aria-1",
                "ARIA button patterns may be incomplete",
                "medium",
                "aria",
                "A link is exposed with role='button' but no keyboard focus cue was detected.",
                "Keyboard users may be unable to activate the control consistently.",
                ["role='button' without supporting keyboard semantics"],
                ["Prefer a native button element or implement the full button keyboard pattern."],
                ["4.1.2", "2.1.1"],
                "interactive-elements",
            )
        )

    if semantic_tags.get("main", 0) == 0:
        issues.append(
            _issue(
                "a11y-semantic-1",
                "Main landmark is missing",
                "low",
                "semantic-html",
                "The page does not expose a main landmark.",
                "Screen reader users may have to traverse more of the page to find the primary content.",
                ["<main> not detected"],
                ["Wrap the primary content in a main element."],
                ["1.3.1", "2.4.1"],
                "document",
            )
        )

    counts = count_by_severity(issues)
    score = score_from_issues(issues)
    summary_parts = []
    if counts["critical"]:
        summary_parts.append(f"{counts['critical']} critical issue(s)")
    if counts["high"]:
        summary_parts.append(f"{counts['high']} high issue(s)")
    if counts["medium"]:
        summary_parts.append(f"{counts['medium']} medium issue(s)")
    if counts["low"]:
        summary_parts.append(f"{counts['low']} low issue(s)")
    if not summary_parts:
        human = "No obvious accessibility defects were detected in the fetched HTML."
    else:
        human = f"Accessibility review found {', '.join(summary_parts)}."
    return {
        "issues": issues,
        "score": score,
        "issue_counts": counts,
        "summary": human,
        "coverage_notes": [
            "Color contrast is best-effort unless the page exposes inline styles or rendered DOM details.",
            "Dynamic JavaScript-only UI may require browser rendering for full verification.",
        ],
    }

