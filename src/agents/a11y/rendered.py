from __future__ import annotations

import logging
import os
from importlib.util import find_spec
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Optional

from .checker import check_accessibility

logger = logging.getLogger(__name__)


def playwright_available() -> bool:
    return find_spec("playwright.sync_api") is not None


def _resolve_axe_source() -> Path | None:
    env_path = os.getenv("PMONO_AXE_CORE_PATH")
    if env_path:
        candidate = Path(env_path)
        if candidate.exists():
            return candidate

    candidates = [
        Path.cwd() / "node_modules" / "axe-core" / "axe.min.js",
        Path(__file__).resolve().parents[4] / "node_modules" / "axe-core" / "axe.min.js",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _run_axe(page) -> dict[str, Any]:
    axe_path = _resolve_axe_source()
    if axe_path is None:
        return {
            "available": False,
            "violations": [],
            "passes": 0,
            "incomplete": 0,
            "coverage_notes": [
                "axe-core script not found. Set PMONO_AXE_CORE_PATH or install axe-core to enable Axe checks.",
            ],
        }

    axe_source = axe_path.read_text(encoding="utf-8", errors="ignore")
    page.add_script_tag(content=axe_source)
    result = page.evaluate(
        """
        async () => {
            if (!window.axe) {
                return { available: false, violations: [], passes: [], incomplete: [] };
            }
            const out = await window.axe.run(document);
            return {
                available: true,
                violations: out.violations.map((item) => ({
                    id: item.id,
                    impact: item.impact,
                    help: item.help,
                    description: item.description,
                    helpUrl: item.helpUrl,
                    nodes: item.nodes.map((node) => ({
                        html: node.html,
                        target: node.target,
                        failureSummary: node.failureSummary,
                    })),
                })),
                passes: out.passes.length,
                incomplete: out.incomplete.length,
            };
        }
        """
    )
    result.setdefault("coverage_notes", [])
    result["coverage_notes"].append("Rendered Axe analysis completed from injected axe-core script.")
    return result


def run_rendered_accessibility_review(
    url: str,
    ai_provider: Optional[Any] = None,
    *,
    html: str | None = None,
) -> dict[str, Any]:
    if not playwright_available():
        return {
            "success": False,
            "audit_type": "rendered-accessibility",
            "url": url,
            "playwright_available": False,
            "axe_available": False,
            "summary": "Playwright is not installed, so rendered-page accessibility review is unavailable.",
            "issues": [],
            "recommendations": [],
            "coverage_notes": [
                "Install playwright to enable browser-rendered accessibility review.",
                "The standard accessibility checker remains available as a fallback.",
            ],
        }

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            if html is not None:
                page.set_content(html, wait_until="load")
                final_url = url or "inline://rendered"
            else:
                page.goto(url, wait_until="networkidle", timeout=60000)
                final_url = page.url
            rendered_html = page.content()
            rendered_tree = None
            try:
                rendered_tree = page.accessibility.snapshot(interesting_only=False)
            except Exception as exc:
                logger.info("Accessibility tree snapshot unavailable: %s", exc)

            rendered_result = check_accessibility(
                final_url,
                ai_provider,
                fetcher=lambda _: SimpleNamespace(html=rendered_html, final_url=final_url),
            )

            axe_result = _run_axe(page)
            if axe_result.get("available"):
                axe_violations = axe_result.get("violations", [])
                if axe_violations:
                    rendered_result["issues"] = rendered_result.get("issues", []) + [
                        {
                            "id": f"axe-{item['id']}",
                            "title": item.get("help", item["id"]),
                            "severity": item.get("impact") or "medium",
                            "category": "axe-core",
                            "description": item.get("description", ""),
                            "impact": item.get("description", ""),
                            "evidence": [node.get("html", "") for node in item.get("nodes", [])[:3]],
                            "recommended_fixes": [node.get("failureSummary", "") for node in item.get("nodes", [])[:3] if node.get("failureSummary")],
                            "wcag_references": [],
                        }
                        for item in axe_violations
                    ]
                    rendered_result["coverage_notes"] = list(
                        dict.fromkeys(
                            list(rendered_result.get("coverage_notes", []))
                            + list(axe_result.get("coverage_notes", []))
                        )
                    )
                    rendered_result["summary"] = (
                        rendered_result.get("summary", "")
                        + f" Axe-core flagged {len(axe_violations)} additional issue(s)."
                    )

            rendered_result["success"] = True
            rendered_result["audit_type"] = "rendered-accessibility"
            rendered_result["playwright_available"] = True
            rendered_result["axe_available"] = bool(axe_result.get("available"))
            rendered_result["rendered_url"] = final_url
            rendered_result["rendered_tree"] = rendered_tree
            rendered_result["rendered_html_length"] = len(rendered_html)
            rendered_result.setdefault("coverage_notes", [])
            rendered_result["coverage_notes"] = list(
                dict.fromkeys(
                    list(rendered_result.get("coverage_notes", []))
                    + [
                        "Browser-rendered HTML was analyzed before heuristic scoring.",
                    ]
                )
            )
            return rendered_result
        except Exception as exc:
            logger.exception("Rendered accessibility review failed")
            return {
                "success": False,
                "audit_type": "rendered-accessibility",
                "url": url,
                "playwright_available": True,
                "axe_available": False,
                "score": 0,
                "summary": f"Rendered accessibility review failed: {exc}",
                "issues": [],
                "recommendations": [],
                "coverage_notes": [str(exc)],
            }
        finally:
            browser.close()
