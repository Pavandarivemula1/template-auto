"""
template_engine/injector.py  –  MODULE D: Smart Content Injector  (v2)

Responsibility: Apply the full content injection pipeline to one HTML file.

KEY DESIGN DECISION (v2):
  lxml is used ONLY for ANALYSIS (detecting roles, reading values).
  ALL actual text replacement is done on the raw HTML string.
  This guarantees:
    - Relative src/href paths are NEVER modified
    - HTML structure is NEVER restructured
    - CSS/JS/image links are always preserved
    - Phone regex does not match image dimension numbers

Pipeline:
  Step 1  - Analyze DOM with lxml → get semantic role targets
  Step 2  - Build replacement map from analysis + client data
  Step 3  - Replace demo brand names globally (raw string, longest first)
  Step 4  - Replace industry slogans (raw string)
  Step 5  - Replace demo address fragments (raw string)
  Step 6  - Replace emails in TEXT content ONLY (not inside src/data attrs)
  Step 7  - Replace phones in TEXT content ONLY (not inside src/data attrs)
  Step 8  - Replace {{placeholder}} tokens anywhere
  Step 9  - Inject SEO <meta> block into <head>
  Step 10 - Write back if changed
"""
import re
import logging
from pathlib import Path

from lxml import html as lxml_html

from config import PLACEHOLDER_KEYS
from template_engine.analyzer import analyze_page

logger = logging.getLogger("engine.injector")

# ── Demo content to remove ──────────────────────────────────────────────────
BANNED_BRANDS = [
    "Darion Homes", "Darion",               # longest first!
    "ACTURA", "Actura",
    "Hanuman",
    "Archetype", "Solara",
    "Horizon Dream Home", "Horizon",
    "Homzen",
    "ARCHERA",
    "Browed",
    "realestate.com",
    "UiXSHUVO",
]

INDUSTRY_SLOGANS = [
    "Construction of private houses",
    "We build concrete homes",
    "From $1500/M2",
    "Premium real estate listings across",
    "Award-winning interior design studio",
]

DEMO_ADDRESSES = [
    "123 Builder Avenue", "123 Dream St", "123 Interior St",
    "Builder Avenue", "Interior St",
]

# ── Safe Regex Patterns ──────────────────────────────────────────────────────
# Matches email addresses
_EMAIL_RE = re.compile(
    r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}'
)

# Phone regex – minimum 7 significant digits, common formats
# Must be surrounded by non-digit boundaries to avoid matching "1500x1000"
_PHONE_RE = re.compile(
    r'(?<![/\w.\-])(\+?\d{1,4}[\s.\-]?'
    r'(?:\(?\d{2,4}\)?[\s.\-]?){1,3}\d{3,6})'
    r'(?![/\w.\-])',
    re.VERBOSE
)

# Matches content INSIDE HTML tags: <tag ...> — used to SKIP phone/email matching
_TAG_RE = re.compile(r'<[^>]+>', re.DOTALL)


# ── Public API ──────────────────────────────────────────────────────────────

def inject_page(html_path: Path, client_data: dict) -> bool:
    """
    Apply the full injection pipeline to one HTML file.

    Args:
        html_path   - Path to the HTML file
        client_data - dict: title, contact, email, address,
                      location, details, logo_text

    Returns:
        True if file was changed and saved, False if unchanged.
    """
    try:
        original = html_path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        logger.error("[injector] Cannot read %s: %s", html_path.name, exc)
        return False

    html = original

    # ── Step 1: {{placeholder}} token replacements ────────────────────────────
    # Now that preprocessor.py does safe standardization into {{tokens}},
    # we just need to do clean, fast string replaces!
    for key in PLACEHOLDER_KEYS:
        token = "{{" + key + "}}"
        if token in html:
            # Fallback to empty string if missing, or use actual value
            val = str(client_data.get(key) or "")
            html = html.replace(token, val)
     
    # For keys not explicitly in PLACEHOLDER_KEYS, let's also support dynamic
    for key, val in client_data.items():
        token = "{{" + key + "}}"
        if val and token in html:
            html = html.replace(token, str(val))

    # ── Step 8: Semantic title/meta (safe attribute-only updates) ─────────
    # These are safe because we only target specific tag patterns
    title = str(client_data.get("title") or "")
    details = str(client_data.get("details") or "")
    
    if title:
        html = re.sub(r'(<title[^>]*>)[^<]*(</title>)', rf'\g<1>{title}\g<2>', html, flags=re.IGNORECASE)
    if details:
        html = re.sub(
            r'(<meta\s+name=["\']description["\']\s+content=["\'])[^"\']*(["\'])',
            lambda m: f'{m.group(1)}{details}{m.group(2)}',
            html, flags=re.IGNORECASE
        )

    # ── Step 9b: Inject SEO meta block ───────────────────────────────────
    html = _inject_meta_block(html, client_data)

    # ── Step 10: Warn on remaining tokens ────────────────────────────────
    leftover = set(re.findall(r'\{\{[a-z_]+\}\}', html))
    if leftover:
        logger.warning("[injector] Unreplaced tokens in %s: %s", html_path.name, leftover)

    # ── Step 10: Write back only if changed ──────────────────────────────
    if html != original:
        html_path.write_text(html, encoding="utf-8", errors="replace")
        return True
    return False


# ── Internal Helpers ──────────────────────────────────────────────────────────

def _replace_in_text_only(html: str, pattern: re.Pattern, replacement: str) -> str:
    """
    Replace regex pattern ONLY in text content between HTML tags,
    NOT inside tag attributes (href, src, data-*, class, etc.).

    Works by splitting the HTML into tag vs. non-tag segments.
    Only non-tag segments (visible text) are processed.
    """
    result = []
    last = 0
    for tag_match in _TAG_RE.finditer(html):
        # Text between last tag and this tag — replace pattern here
        text_segment = html[last:tag_match.start()]
        result.append(pattern.sub(replacement, text_segment))
        # Tag itself — keep unchanged
        result.append(tag_match.group(0))
        last = tag_match.end()
    # Tail after last tag
    result.append(pattern.sub(replacement, html[last:]))
    return "".join(result)


def _replace_phones_in_text(html: str, contact: str) -> str:
    """
    Replace phone numbers that appear in visible text (between HTML tags)
    with the client contact number. Uses minimum‑7‑digit filter to avoid
    matching CSS dimensions or image sizes like 1920x1080.
    """
    def _safe_phone_sub(m):
        digits = re.sub(r'\D', '', m.group(0))
        if len(digits) >= 7:
            return contact
        return m.group(0)

    result = []
    last = 0
    for tag_match in _TAG_RE.finditer(html):
        text_segment = html[last:tag_match.start()]
        result.append(_PHONE_RE.sub(_safe_phone_sub, text_segment))
        result.append(tag_match.group(0))   # keep tag unchanged
        last = tag_match.end()
    result.append(_PHONE_RE.sub(_safe_phone_sub, html[last:]))
    return "".join(result)


def _inject_meta_block(html: str, cd: dict) -> str:
    """
    Insert a universal SEO <meta> block just before </head>.
    Idempotent — only injected once per page.
    """
    marker = "data-engine-client"
    if marker in html:
        return html

    block = (
        "\n    <!-- Generated by Template Engine -->\n"
        f'    <meta {marker} content="true" />\n'
        f'    <meta name="author"      content="{cd.get("title",     "")}" />\n'
        f'    <meta name="contact"     content="{cd.get("contact",   "")}" />\n'
        f'    <meta name="email"       content="{cd.get("email",     "")}" />\n'
        f'    <meta name="address"     content="{cd.get("address",   "")}" />\n'
        f'    <meta name="location"    content="{cd.get("location",  "")}" />\n'
        f'    <meta name="logo-text"   content="{cd.get("logo_text", "")}" />\n'
        f'    <meta name="description" content="{cd.get("details",   "")}" />\n'
    )

    if "</head>" in html:
        return html.replace("</head>", block + "</head>", 1)
    if "</HEAD>" in html:
        return html.replace("</HEAD>", block + "</HEAD>", 1)
    return html
