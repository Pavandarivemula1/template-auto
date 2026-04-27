"""
template_engine/detector.py  –  MODULE C: Pattern Detector

Responsibility: Pure regex-based detection of phones, emails,
banned brand names, and placeholder tokens in raw HTML strings.

These functions are stateless utility helpers used by the injector
to decide WHAT to replace before touching the DOM.

Usage:
    from template_engine.detector import detect_phones, detect_emails, detect_brands
"""
import re
import logging
from typing import NamedTuple

logger = logging.getLogger("engine.detector")

# ── Compiled regex patterns ─────────────────────────────────────────────────

# Matches international phone formats:
# +91 9000011111 / (406) 555-0120 / +1-800-555-1234 / 080-1234-5678
PHONE_RE = re.compile(
    r'(?<!\d)(\+?\d{1,4}[\s.\-]?'     # optional country code
    r'(?:\(?\d{2,4}\)?[\s.\-]?){1,3}'  # area + groups
    r'\d{3,6})(?!\d)',
    re.VERBOSE
)

# Standard email format
EMAIL_RE = re.compile(
    r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}'
)

# Standard {{key}} placeholder tokens
PLACEHOLDER_RE = re.compile(r'\{\{([a-z_]+)\}\}')


class Match(NamedTuple):
    """Represents a detected string match with its value and location."""
    value: str       # The matched string
    start: int       # Character index in the source HTML
    end:   int       # Character index after the match


# ── Public API ──────────────────────────────────────────────────────────────

def detect_phones(html: str) -> list[Match]:
    """
    Return all phone-number-like strings found in raw HTML.

    Filters out matches shorter than 8 characters (avoids false positives
    like CSS values "0 10px 0 0" matching the regex).
    """
    results = []
    for m in PHONE_RE.finditer(html):
        value = m.group(0).strip()
        if len(re.sub(r'\D', '', value)) >= 7:   # at least 7 digits
            results.append(Match(value, m.start(), m.end()))
    return results


def detect_emails(html: str) -> list[Match]:
    """Return all email-address-like strings found in raw HTML."""
    return [
        Match(m.group(0), m.start(), m.end())
        for m in EMAIL_RE.finditer(html)
    ]


def detect_brands(html: str, banned_brands: list[str]) -> list[Match]:
    """
    Return all occurrences of any banned brand string in the raw HTML.
    Sorted longest-first to avoid partial-replacement bugs
    (e.g. replace 'Darion Homes' before 'Darion').
    """
    results = []
    for brand in sorted(banned_brands, key=len, reverse=True):
        pattern = re.compile(re.escape(brand), re.IGNORECASE)
        for m in pattern.finditer(html):
            results.append(Match(brand, m.start(), m.end()))
    return results


def detect_placeholders(html: str) -> list[Match]:
    """Return all {{key}} placeholder tokens found in the raw HTML."""
    return [
        Match(m.group(0), m.start(), m.end())
        for m in PLACEHOLDER_RE.finditer(html)
    ]


def has_banned_in_visible(html: str, banned_brands: list[str]) -> list[str]:
    """
    Check if any banned brands appear in VISIBLE content only
    (strips <style>, <script>, and HTML comments before checking).
    Returns list of banned strings that are still present.
    """
    # Remove non-visible content
    visible = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.IGNORECASE | re.DOTALL)
    visible = re.sub(r'<script[^>]*>.*?</script>', '', visible, flags=re.IGNORECASE | re.DOTALL)
    visible = re.sub(r'<!--.*?-->', '', visible, flags=re.DOTALL)

    surviving = []
    for brand in banned_brands:
        if brand.lower() in visible.lower():
            surviving.append(brand)
    return surviving
