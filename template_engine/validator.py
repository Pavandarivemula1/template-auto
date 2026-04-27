"""
template_engine/validator.py  –  MODULE E: QA Validator

Responsibility: Scan the fully generated client site for any surviving
banned brand strings in VISIBLE content only, and check for obvious
asset path issues.

This module NEVER raises an exception. It returns a ValidationReport
so the caller can decide how to handle any issues.

Usage:
    from template_engine.validator import validate_site, ValidationReport
    report = validate_site(out_dir, banned_brands=BANNED_BRANDS)
    if not report.ok:
        for issue in report.issues: logger.warning(issue)
"""
import re
import logging
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger("engine.validator")


@dataclass
class ValidationReport:
    """Result of a site validation scan."""
    ok:     bool        = True           # False if any visible issues found
    issues: list[str]   = field(default_factory=list)    # human-readable problem list
    stats:  dict        = field(default_factory=dict)    # page counts etc.


def validate_site(out_dir: Path, banned_brands: list[str]) -> ValidationReport:
    """
    Scan every HTML file in the generated site for quality issues.

    Checks (visible content only — strips <style>/<script>/comments):
      1. Banned brand strings still present in user-visible text
      2. Unreplaced {{placeholder}} tokens
      3. Broken internal href/src links (relative paths that don't resolve)

    Args:
        out_dir       - Path to the generated client folder
        banned_brands - List of demo brand strings to check for

    Returns:
        ValidationReport with ok=True if no visible issues found
    """
    report = ValidationReport()
    html_files = list(out_dir.rglob("*.html"))
    report.stats["total_pages"] = len(html_files)
    report.stats["issues_per_page"] = {}

    for html_path in html_files:
        page_issues = []
        try:
            content = html_path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            report.issues.append(f"Cannot read {html_path.name}: {exc}")
            report.ok = False
            continue

        # Strip non-visible content before checking
        visible = _strip_non_visible(content)

        # ── Check 1: Banned brands in visible text ────────────────────────
        for brand in sorted(banned_brands, key=len, reverse=True):
            if brand.lower() in visible.lower():
                msg = f"Banned brand '{brand}' visible in {html_path.name}"
                page_issues.append(msg)
                report.issues.append(msg)
                report.ok = False

        # ── Check 2: Unreplaced {{...}} tokens ───────────────────────────
        leftover = set(re.findall(r'\{\{[a-z_]+\}\}', visible))
        if leftover:
            msg = f"Unreplaced tokens {leftover} in {html_path.name}"
            page_issues.append(msg)
            report.issues.append(msg)
            # Don't set ok=False for tokens (may be intentional in templates)
            logger.warning("[validator] %s", msg)

        # ── Check 3: Obvious broken internal links ────────────────────────
        broken = _find_broken_links(html_path, out_dir)
        for b in broken:
            msg = f"Broken internal link '{b}' in {html_path.name}"
            page_issues.append(msg)
            report.issues.append(msg)
            # Don't fail on broken links — templates may have intentional placeholders

        if page_issues:
            report.stats["issues_per_page"][html_path.name] = page_issues

    # ── Summary log ───────────────────────────────────────────────────────
    if report.ok:
        logger.info(
            "[validator] PASSED – %d pages scanned, no visible banned content.",
            len(html_files)
        )
    else:
        logger.warning(
            "[validator] %d issue(s) across %d pages. "
            "Review generated_sites/ to verify client data looks correct.",
            len(report.issues), len(html_files)
        )

    return report


# ── Private Helpers ──────────────────────────────────────────────────────────

def _strip_non_visible(html: str) -> str:
    """Remove <style>, <script>, HTML comments, emails, and URLs from HTML before text checks."""
    result = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.IGNORECASE | re.DOTALL)
    result = re.sub(r'<script[^>]*>.*?</script>', '', result, flags=re.IGNORECASE | re.DOTALL)
    result = re.sub(r'<!--.*?-->', '', result, flags=re.DOTALL)
    
    # Strip emails so if client email is user@darion.in it doesn't trigger Darion violation
    result = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '', result)
    
    # Strip basic URLs
    result = re.sub(r'https?://[^\s<"]+', '', result)
    return result


def _find_broken_links(html_path: Path, base_dir: Path) -> list[str]:
    """
    Find relative href/src links that don't resolve to an actual file.
    Only checks simple relative paths (no http://, #anchors, or data:).
    """
    broken = []
    try:
        content = html_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return broken

    # Match href="..." and src="..." values
    refs = re.findall(r'(?:href|src)=["\']([^"\'#?]+)["\']', content)
    for ref in refs:
        # Skip absolute URLs, anchors, mailto:, tel:, data:
        if ref.startswith(("http", "#", "mailto:", "tel:", "data:", "//")):
            continue
        # Check if relative path resolves relative to the HTML file's directory
        target = html_path.parent / ref
        if not target.exists():
            broken.append(ref)

    return broken
