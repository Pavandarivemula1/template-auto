"""
template_engine/analyzer.py  –  MODULE B: DOM Structure Analyzer

Responsibility: Parse an HTML file with lxml.html and inspect its DOM
structure to detect which elements play which business roles.

Key roles detected:
  logo    - navbar brand / header logo text
  hero_h1 - main hero heading (H1)
  hero_p  - hero subtitle paragraph
  footer_p - company description in footer
  contact_links - <a href="tel:..."> elements
  email_links   - <a href="mailto:..."> elements

Returns a DetectionResult dict that the Injector uses to make
targeted, semantic replacements instead of brute-force text search.

Usage:
    from template_engine.analyzer import analyze_page
    result = analyze_page(Path("path/to/page.html"))
"""
import logging
from dataclasses import dataclass, field
from pathlib import Path

from lxml import html as lxml_html
from lxml.html import HtmlElement

logger = logging.getLogger("engine.analyzer")

# CSS class keywords that identify logo / brand elements
_LOGO_CLASSES  = {"navbar-brand", "logo", "brand", "header__logo", "site-logo", "nav-brand"}
# CSS class keywords that identify hero / banner sections
_HERO_CLASSES  = {"hero", "banner", "slider", "main-title", "slider-content", "jumbotron"}
# CSS class keywords that identify footer content
_FOOTER_CLASSES = {"footer", "footer-about", "company-info", "footer-description", "site-footer"}
# CSS class keywords that identify contact info blocks
_CONTACT_CLASSES = {"contact", "contact-info", "info-box", "address-block", "footer-contact"}


@dataclass
class DetectionResult:
    """
    Carries detected DOM elements per semantic role.

    Each list contains lxml HtmlElement objects that will be targeted
    for content replacement by the injector.
    """
    logo_elements:     list = field(default_factory=list)   # brand/logo text nodes
    hero_h1_elements:  list = field(default_factory=list)   # main page H1
    hero_p_elements:   list = field(default_factory=list)   # hero subtitle paragraphs
    footer_p_elements: list = field(default_factory=list)   # footer about paragraphs
    tel_links:         list = field(default_factory=list)   # <a href="tel:...">
    mailto_links:      list = field(default_factory=list)   # <a href="mailto:...">
    title_element:     list = field(default_factory=list)   # <title>
    meta_desc:         list = field(default_factory=list)   # <meta name="description">


def analyze_page(html_path: Path) -> DetectionResult:
    """
    Parse an HTML file and return a DetectionResult describing
    which elements map to which business identity roles.

    Args:
        html_path - absolute Path to an HTML file

    Returns:
        DetectionResult with lists of matched lxml elements per role
    """
    result = DetectionResult()

    try:
        content = html_path.read_text(encoding="utf-8", errors="replace")
        doc = lxml_html.fromstring(content)
    except Exception as exc:
        logger.error("[analyzer] Cannot parse %s: %s", html_path.name, exc)
        return result

    # ── <title> ──────────────────────────────────────────────────────────
    for el in doc.cssselect("title"):
        result.title_element.append(el)

    # ── <meta name="description"> ─────────────────────────────────────────
    for el in doc.cssselect('meta[name="description"]'):
        result.meta_desc.append(el)

    # ── Logo / Brand ──────────────────────────────────────────────────────
    # Strategy: match any element whose class contains a logo-related keyword
    for el in doc.iter():
        classes = _get_classes(el)
        if classes & _LOGO_CLASSES:
            # We want the leaf text node. If it's a div containing an svg and a text node
            # we should add the element that actually contains the text.
            text_leaves = [child for child in el.iter() if child.text and child.text.strip() and not list(child)]
            if text_leaves:
                result.logo_elements.extend(text_leaves)
            else:
                result.logo_elements.append(el)

    # ── Hero / Banner ─────────────────────────────────────────────────────
    # Only replace H1 hero titles on index.html to avoid destroying inner page H1s like "Rent Properties"
    if html_path.name.lower() == "index.html":
        for el in doc.iter():
            classes = _get_classes(el)
            if classes & _HERO_CLASSES:
                # Collect H1 elements inside hero sections
                for h1 in el.cssselect("h1"):
                    result.hero_h1_elements.append(h1)
                # Collect paragraphs that are direct children of hero sections
                for p in el.cssselect("p"):
                    if _text_length(p) > 15:   # skip short/icon-only tags
                        result.hero_p_elements.append(p)

        # Fallback: if no hero H1 found above on index, grab the first H1
        if not result.hero_h1_elements:
            for h1 in doc.cssselect("h1"):
                result.hero_h1_elements.append(h1)
                break   # only the first one

    # ── Footer ────────────────────────────────────────────────────────────
    for el in doc.iter():
        classes = _get_classes(el)
        if classes & _FOOTER_CLASSES:
            for p in el.cssselect("p"):
                if _text_length(p) > 15:
                    result.footer_p_elements.append(p)

    # Also catch the standard <footer> tag
    for footer in doc.cssselect("footer"):
        for p in footer.cssselect("p"):
            if _text_length(p) > 15 and p not in result.footer_p_elements:
                result.footer_p_elements.append(p)

    # ── Contact Links ─────────────────────────────────────────────────────
    for a in doc.cssselect('a[href^="tel:"]'):
        result.tel_links.append(a)

    # ── Email Links ───────────────────────────────────────────────────────
    for a in doc.cssselect('a[href^="mailto:"]'):
        result.mailto_links.append(a)

    logger.debug(
        "[analyzer] %s → logos=%d h1=%d hero_p=%d footer_p=%d tel=%d mailto=%d",
        html_path.name,
        len(result.logo_elements), len(result.hero_h1_elements),
        len(result.hero_p_elements), len(result.footer_p_elements),
        len(result.tel_links), len(result.mailto_links),
    )

    return result


# ── Private Helpers ──────────────────────────────────────────────────────────

def _get_classes(el) -> set:
    """Return a set of lowercased CSS class tokens for an lxml element."""
    if not isinstance(el, HtmlElement):
        return set()
    class_attr = el.get("class", "")
    return {c.lower() for c in class_attr.split()}


def _text_length(el) -> int:
    """Return approximate visible text character count within an element."""
    return len((el.text_content() or "").strip())
