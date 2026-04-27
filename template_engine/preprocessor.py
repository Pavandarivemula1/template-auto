"""
template_engine/preprocessor.py  –  Template Preprocessing Engine

ONE-TIME OPERATION: Run this BEFORE any client generation.

Purpose:
  Analyze a raw imported demo template folder, detect all hardcoded
  business content using lxml DOM analysis + regex, replace it with
  universal {{placeholder}} tokens, and save a template_map.json
  structural config alongside the cleaned HTML files.

After preprocessing:
  - Templates contain {{title}}, {{contact}}, {{email}} etc.
  - Client injection becomes a trivial string.replace()
  - No more fragile per-generation semantic detection

Usage:
  from template_engine.preprocessor import preprocess_template
  report = preprocess_template("2")   # processes templates/2/
  report = preprocess_template("r-8") # processes templates/r-8/
"""
import re
import json
import logging
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field, asdict

from lxml import html as lxml_html

from config import TEMPLATES_DIR, VALID_TEMPLATES

logger = logging.getLogger("engine.preprocessor")

# ── Known demo brand names to always replace ────────────────────────────────
KNOWN_DEMO_BRANDS = [
    "Darion Homes", "Darion",
    "ACTURA", "Actura",
    "Hanuman",
    "Archetype Solara", "Archetype · Solara",   # longest first
    "Archetype", "Solara",
    "Horizon Dream Home", "Horizon",
    "Homzen",
    "ARCHERA",
    "Browed",
    "UiXSHUVO",
    "Compatto",
]

# Demo slogans / industry-specific phrases to replace with {{details}}
KNOWN_DEMO_SLOGANS = [
    "Construction of private houses",
    "We build concrete homes",
    "From $1500/M2",
    "FROM $1500/M2",
    "Premium real estate listings across",
    "Award-winning interior design studio",
    "Connecting you to the home you love",
    "Discover the best properties with our tailored",
    "Find Your Dream Property",
]

# Demo addresses to replace with {{address}}
KNOWN_DEMO_ADDRESSES = [
    "123 Builder Avenue",
    "123 Dream St",
    "123 Interior St",
    "43-18 97th Pl",
    "Builder Avenue",
]

# Regex for detecting live contact info
_EMAIL_RE = re.compile(
    r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}'
)
# Phone: must contain a run of at least 6 consecutive digits to distinguish
# from SVG path data like '9 22 9 12 15 12' which has isolated digit groups
_PHONE_RE = re.compile(
    r'(?<![/\w.\-])'           # not inside a path/attribute
    r'(\+?\d{6,}'              # at least 6 consecutive digits (with optional +)
    r'|\+?\d{1,4}[\s.\-]?'    # OR country code + separator
    r'\(?\d{3,4}\)?[\s.\-]?'  # area code
    r'\d{3,4}[\s.\-]?'        # local prefix
    r'\d{4,6})'                # last group
    r'(?![/\w.\-])',
    re.VERBOSE
)

# CSS classes that indicate logo/brand elements
_LOGO_CLASSES = {"navbar-brand", "logo", "brand", "logo-title", "site-logo", "header__logo", "logo-text"}
# CSS classes for hero / banner sections
_HERO_CLASSES  = {"hero", "banner", "slider", "hero-content", "main-slide", "slider-content", "jumbotron"}
# CSS classes for footer description
_FOOTER_CLASSES = {"footer-about", "footer-desc", "footer-description", "footer__about", "footer-brand"}


# ── Result dataclasses ────────────────────────────────────────────────────────

@dataclass
class PlaceholderMapping:
    """Records what was detected and what it was replaced with."""
    placeholder: str         # e.g. "{{title}}"
    original_value: str      # e.g. "ACTURA"
    selector: str = ""       # CSS selector where found (if via DOM)
    count: int = 0           # how many replacements were made


@dataclass
class PreprocessReport:
    """Full preprocessing result for one template."""
    template_name:  str
    processed_at:   str
    pages_processed: int     = 0
    pages_modified:  int     = 0
    mappings:        list    = field(default_factory=list)   # list of PlaceholderMapping
    detected_emails: list    = field(default_factory=list)
    detected_phones: list    = field(default_factory=list)
    detected_brands: list    = field(default_factory=list)
    ok:              bool    = True
    errors:          list    = field(default_factory=list)


# ── Public API ──────────────────────────────────────────────────────────────

def preprocess_template(template_name: str, dry_run: bool = False) -> PreprocessReport:
    """
    Preprocess one template folder: detect all demo content and replace
    with {{placeholders}}. Saves modified HTML in-place and writes a
    template_map.json.

    Args:
        template_name - folder under templates/ (e.g. "2", "r-8")
        dry_run       - if True, detect and report but do NOT write changes

    Returns:
        PreprocessReport with detection results and success/error info
    """
    report = PreprocessReport(
        template_name=template_name,
        processed_at=datetime.now().isoformat(timespec="seconds"),
    )

    tmpl_dir = TEMPLATES_DIR / template_name
    if not tmpl_dir.is_dir():
        report.ok = False
        report.errors.append(f"Template folder not found: {tmpl_dir}")
        logger.error("[preprocessor] %s", report.errors[-1])
        return report

    html_files = list(tmpl_dir.rglob("*.html"))
    report.pages_processed = len(html_files)
    logger.info("[preprocessor] Processing %s: %d HTML pages", template_name, len(html_files))

    # ── Phase 1: Auto-detect demo values from index.html ─────────────────
    index_path = tmpl_dir / "index.html"
    auto_detected = _detect_demo_values(index_path) if index_path.exists() else {}
    logger.info("[preprocessor] Auto-detected from index.html: %s", auto_detected)

    # ── Phase 2: Build replacement table ─────────────────────────────────
    # priority: longest strings first to avoid partial matches
    replacements: list[tuple[str, str, str]] = []  # (original, placeholder, label)

    # Known demo brands → {{title}}
    for brand in sorted(KNOWN_DEMO_BRANDS, key=len, reverse=True):
        replacements.append((brand, "{{title}}", "brand"))
        report.detected_brands.append(brand)

    # Auto-detected brand from DOM → {{logo_text}}
    if auto_detected.get("logo_text") and auto_detected["logo_text"] not in KNOWN_DEMO_BRANDS:
        replacements.insert(0, (auto_detected["logo_text"], "{{logo_text}}", "logo_auto"))

    # Known demo slogans → {{details}}
    for slogan in sorted(KNOWN_DEMO_SLOGANS, key=len, reverse=True):
        replacements.append((slogan, "{{details}}", "slogan"))

    # Known demo addresses → {{address}}
    for addr in sorted(KNOWN_DEMO_ADDRESSES, key=len, reverse=True):
        replacements.append((addr, "{{address}}", "address"))

    # Auto-detected email → {{email}}
    if auto_detected.get("email"):
        replacements.append((auto_detected["email"], "{{email}}", "email_auto"))
        report.detected_emails.append(auto_detected["email"])

    # Auto-detected phone → {{contact}}
    if auto_detected.get("phone"):
        replacements.append((auto_detected["phone"], "{{contact}}", "phone_auto"))
        report.detected_phones.append(auto_detected["phone"])

    # ── Phase 3: Process each HTML file ───────────────────────────────────
    for html_path in html_files:
        _process_one_html(html_path, replacements, report, dry_run)

    # ── Phase 4: Save template_map.json ───────────────────────────────────
    if not dry_run:
        _save_template_map(tmpl_dir, report)

    logger.info(
        "[preprocessor] %s done: %d/%d pages modified, %d mappings applied",
        template_name, report.pages_modified, report.pages_processed, len(report.mappings)
    )
    return report


def preprocess_all(dry_run: bool = False) -> dict[str, PreprocessReport]:
    """
    Preprocess ALL valid templates. Returns a dict of template_name → report.
    Skip the 'ui' folder (it's the admin UI, not a user template).
    """
    results = {}
    for tmpl_name in sorted(VALID_TEMPLATES):
        if tmpl_name == "ui":
            continue
        logger.info("[preprocessor] === Preprocessing template: %s ===", tmpl_name)
        results[tmpl_name] = preprocess_template(tmpl_name, dry_run=dry_run)
    return results


# ── Internal Helpers ──────────────────────────────────────────────────────────

def _detect_demo_values(index_path: Path) -> dict:
    """
    Use lxml to parse index.html and find the template's actual demo values.
    Returns a dict: { "logo_text": ..., "email": ..., "phone": ... }
    """
    detected = {}
    try:
        content = index_path.read_text(encoding="utf-8", errors="replace")
        doc = lxml_html.fromstring(content)
    except Exception as exc:
        logger.warning("[preprocessor] Cannot parse index.html: %s", exc)
        return detected

    # Find logo text
    for el in doc.iter():
        classes = set((el.get("class") or "").lower().split())
        if classes & _LOGO_CLASSES:
            text = (el.text_content() or "").strip()
            # Only accept if it looks like a brand name: 3-30 chars, not all lowercase common words
            if 3 <= len(text) <= 40 and not text.lower().startswith(("home", "about", "contact", "nav")):
                detected["logo_text"] = text
                break

    # Find email
    emails = _EMAIL_RE.findall(content)
    # filter out obvious non-business emails (google fonts, cdn etc)
    business_emails = [e for e in emails if not any(x in e for x in ["google", "googleapis", "gstatic", "cloudflare", "unsplash"])]
    if business_emails:
        detected["email"] = business_emails[0]

    # Find phone: prefer tel: href values
    for a in doc.cssselect('a[href^="tel:"]'):
        ph = a.get("href", "").replace("tel:", "").strip()
        if len(re.sub(r'\D', '', ph)) >= 7:
            detected["phone"] = ph
            break

    # Fallback: regex scan for phone in text
    if "phone" not in detected:
        phones = _PHONE_RE.findall(content)
        valid_phones = [p for p in phones if len(re.sub(r'\D', '', p)) >= 7]
        if valid_phones:
            detected["phone"] = valid_phones[0]

    return detected


def _process_one_html(
    html_path: Path,
    replacements: list[tuple[str, str, str]],
    report: PreprocessReport,
    dry_run: bool,
):
    """
    Apply all text replacements to a single HTML file.
    Works purely on the raw string to preserve structure perfectly.
    Skips replacements inside src= and non-text attributes to avoid breaking image links.
    """
    try:
        original = html_path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        report.errors.append(f"Cannot read {html_path.name}: {exc}")
        return

    html = original

    for orig, placeholder, label in replacements:
        if not orig or placeholder in orig:  # don't replace if already a placeholder
            continue
        if orig.lower() in html.lower():
            count_before = html.lower().count(orig.lower())

            # Replace safely – only in text nodes, not inside src/data attributes
            html = _safe_replace(html, orig, placeholder)

            count_after = html.lower().count(orig.lower())
            count_replaced = count_before - count_after

            if count_replaced > 0:
                # Record in report (avoid duplicates)
                existing = next(
                    (m for m in report.mappings if m["original"] == orig and m["placeholder"] == placeholder),
                    None
                )
                if existing:
                    existing["count"] += count_replaced
                else:
                    report.mappings.append({
                        "original": orig,
                        "placeholder": placeholder,
                        "label": label,
                        "count": count_replaced,
                    })

    # Also replace ALL remaining emails with {{email}}
    if _EMAIL_RE.search(html):
        html = _replace_emails_in_text(html)

    # Replace remaining phones with {{contact}}
    html = _replace_phones_in_text(html)

    # Write only if changed
    if html != original:
        report.pages_modified += 1
        if not dry_run:
            html_path.write_text(html, encoding="utf-8", errors="replace")
            logger.debug("[preprocessor] Modified: %s", html_path.name)


def _safe_replace(html: str, original: str, replacement: str) -> str:
    """
    Replace `original` with `replacement` in:
      ✓ Text content between HTML tags (visible text)
      ✓ meta content="..." attribute values (SEO meta tags, og: tags)
      ✓ <title> tag text
      ✗ src, href, class, id, data-*, style attributes (preserved intact)

    This ensures brand names hidden in meta/title tags are also cleared,
    even if they don't appear in visible body text.
    """
    _TAG_RE = re.compile(r'<[^>]+>', re.DOTALL)
    escaped = re.escape(original)

    # ── Step A: Replace in meta content= attribute values ───────────────
    # Targets: <meta name="..." content="... Brand ...">
    #          <meta property="og:title" content="Brand">
    def _replace_in_meta_content(tag: str) -> str:
        tag_lower = tag.lower()
        if not tag_lower.startswith("<meta"):
            return tag
        # Only replace inside content="..." attribute
        return re.sub(
            r'(content=["\'])([^"\']*?)(["\'])',
            lambda m: m.group(1) + re.sub(escaped, replacement, m.group(2), flags=re.IGNORECASE) + m.group(3),
            tag,
            flags=re.IGNORECASE,
        )

    # ── Step B: Replace in <title>...</title> ────────────────────────
    html = re.sub(
        r'(<title[^>]*>)(.*?)(</title>)',
        lambda m: m.group(1) + re.sub(escaped, replacement, m.group(2), flags=re.IGNORECASE) + m.group(3),
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )

    # ── Step C: Replace in text nodes + meta content= attrs ─────────
    parts = []
    last = 0
    for tag_m in _TAG_RE.finditer(html):
        text_seg = html[last:tag_m.start()]
        # Replace in text segment
        text_seg = re.sub(escaped, replacement, text_seg, flags=re.IGNORECASE)
        parts.append(text_seg)

        # Replace inside meta content= attrs; keep everything else unchanged
        tag = _replace_in_meta_content(tag_m.group(0))
        parts.append(tag)
        last = tag_m.end()

    # Tail after last tag
    tail = html[last:]
    tail = re.sub(escaped, replacement, tail, flags=re.IGNORECASE)
    parts.append(tail)

    return "".join(parts)



def _replace_emails_in_text(html: str) -> str:
    """Replace all email addresses in visible text with {{email}}, skip src/data attrs."""
    _TAG_RE = re.compile(r'<[^>]+>', re.DOTALL)
    parts = []
    last = 0
    for tag_m in _TAG_RE.finditer(html):
        text_seg = html[last:tag_m.start()]
        text_seg = _EMAIL_RE.sub("{{email}}", text_seg)
        parts.append(text_seg)

        # Update mailto: hrefs inside the tag
        tag = tag_m.group(0)
        tag = re.sub(r'(href=["\']mailto:)[^"\']+(["\'])', r'\g<1>{{email}}\g<2>', tag)
        parts.append(tag)
        last = tag_m.end()
    tail = _EMAIL_RE.sub("{{email}}", html[last:])
    parts.append(tail)
    return "".join(parts)


def _replace_phones_in_text(html: str) -> str:
    """Replace phone numbers in visible text with {{contact}}, skip src/data attrs."""
    _TAG_RE = re.compile(r'<[^>]+>', re.DOTALL)

    def _sub_phone(m):
        digits = re.sub(r'\D', '', m.group(0))
        if len(digits) >= 7:
            return "{{contact}}"
        return m.group(0)

    parts = []
    last = 0
    for tag_m in _TAG_RE.finditer(html):
        text_seg = html[last:tag_m.start()]
        text_seg = _PHONE_RE.sub(_sub_phone, text_seg)
        parts.append(text_seg)

        # Update tel: hrefs
        tag = tag_m.group(0)
        tag = re.sub(r'(href=["\']tel:)[^"\']+(["\'])', r'\g<1>{{contact}}\g<2>', tag)
        parts.append(tag)
        last = tag_m.end()

    tail = _PHONE_RE.sub(_sub_phone, html[last:])
    parts.append(tail)
    return "".join(parts)


def _save_template_map(tmpl_dir: Path, report: PreprocessReport):
    """Write template_map.json to the template folder."""
    data = {
        "template_name": report.template_name,
        "processed_at": report.processed_at,
        "pages_processed": report.pages_processed,
        "pages_modified": report.pages_modified,
        "detected_brands": report.detected_brands,
        "detected_emails": report.detected_emails,
        "detected_phones": report.detected_phones,
        "placeholder_mappings": report.mappings,
        "errors": report.errors,
    }
    out_path = tmpl_dir / "template_map.json"
    out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("[preprocessor] Saved: %s", out_path)
