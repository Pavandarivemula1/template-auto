"""
fix_placeholders.py
-------------------
Robust placeholder injection for all 9 real-estate templates.
Scans each index.html, finds the actual text in key positions,
and stamps the four {{tokens}} in multiple spots per template.

Run:  python fix_placeholders.py
"""
from pathlib import Path
import re

BASE = Path(__file__).parent / "templates"

def patch(folder: str, patches: list[tuple[str,str]]):
    path = BASE / folder / "index.html"
    if not path.exists():
        print(f"[SKIP] {folder}: no index.html"); return
    html = path.read_text(encoding="utf-8", errors="replace")
    applied = 0
    for old, new in patches:
        if old in html:
            html = html.replace(old, new)
            applied += 1
        else:
            pass  # silently skip non-matching strings
    path.write_text(html, encoding="utf-8")
    print(f"[{folder}] {applied}/{len(patches)} replacements applied")

# ── 1 · Archetype / Solara ──────────────────────────────────────────────────
patch("1", [
    # Title
    ("Archetype | Solara Theme - Visionary Architecture & Design", "{{title}}"),
    ("Archetype | Solara Theme - Visionary Architecture &amp; Design", "{{title}}"),
    # Logo text (inside <a class="logo">)
    (">ARCHETYPE<", ">{{title}}<"),
    # Hero description
    ("An award-winning architectural design firm specializing in sustainable luxury, bespoke residential retreats, and visionary commercial environments.",
     "{{details}}"),
    # Footer brand
    ("© 2026 Archetype. All rights reserved.", "© 2026 {{title}}. All rights reserved."),
    # Footer address/tagline
    ("Sculpting Light, Defining Space. | Guntur, AP", "{{address}}"),
    # WhatsApp contact
    ("919876543210", "{{contact}}"),
    # Meta author
    ('content="Archetype"', 'content="{{title}}"'),
])

# ── 2 · Actura · Construction ───────────────────────────────────────────────
# Read actual HTML first
_p2 = (BASE / "2" / "index.html").read_text(encoding="utf-8", errors="replace")

# Find logo text
_logo2 = re.search(r'class="logo[^"]*"[^>]*>\s*<[^>]+>\s*([A-Z][A-Za-z ]+)', _p2)
_logo2_txt = _logo2.group(1).strip() if _logo2 else ""

# Find phone/email line
_phone2 = re.search(r'(\+[\d\s\(\)\-]{7,})', _p2)
_phone2_txt = _phone2.group(1).strip() if _phone2 else ""

# Find address in footer
_addr2 = re.search(r'(\d+\s+[A-Za-z ,\.]+(?:Street|Ave|Blvd|Road|Rd)[A-Za-z ,\.]*)', _p2)
_addr2_txt = _addr2.group(1).strip() if _addr2 else ""

# Find email
_email2 = re.search(r'[\w\.\-]+@[\w\.\-]+\.[a-z]{2,}', _p2)
_email2_txt = _email2.group(0).strip() if _email2 else ""

_patches2 = [
    ("<title>Actura - Construction</title>", "<title>{{title}}</title>"),
]
if _logo2_txt:  _patches2.append((_logo2_txt, "{{title}}"))
if _phone2_txt: _patches2.append((_phone2_txt, "{{contact}}"))
if _addr2_txt:  _patches2.append((_addr2_txt, "{{address}}"))
if _email2_txt: _patches2.append((_email2_txt, "{{contact}}"))
# Footer copyright
for brand in ["Actura", "ACTURA"]:
    _patches2.append((f"© 2026 {brand}", f"© 2026 {{{{title}}}}"))
    _patches2.append((f"© 2025 {brand}", f"© 2026 {{{{title}}}}"))
    _patches2.append((f"© 2024 {brand}", f"© 2026 {{{{title}}}}"))
patch("2", _patches2)

# ── 3 · Generic Real Estate Construction ────────────────────────────────────
_p3 = (BASE / "3" / "index.html").read_text(encoding="utf-8", errors="replace")
_phone3 = re.search(r'(\+[\d\s\(\)\-]{7,}|[\d\-\(\) ]{10,})', _p3)
_phone3_txt = _phone3.group(1).strip() if _phone3 else ""
_email3 = re.search(r'[\w\.\-]+@[\w\.\-]+\.[a-z]{2,}', _p3)
_email3_txt = _email3.group(0) if _email3 else ""

patch("3", [
    ("<title>Real Estate - Construction Company</title>", "<title>{{title}}</title>"),
    *([(_phone3_txt, "{{contact}}")] if _phone3_txt else []),
    *([(_email3_txt, "{{contact}}")] if _email3_txt else []),
])

# ── 4 · Horizon ─────────────────────────────────────────────────────────────
_p4 = (BASE / "4" / "index.html").read_text(encoding="utf-8", errors="replace")
_email4 = re.search(r'[\w\.\-]+@[\w\.\-]+\.[a-z]{2,}', _p4)
_phone4 = re.search(r'(\+[\d\s\(\)\-]{8,})', _p4)

patch("4", [
    ("<title>Horizon | Discover Your Dream Home</title>", "<title>{{title}} | Real Estate</title>"),
    (">Horizon<", ">{{title}}<"),
    *([(_email4.group(0), "{{contact}}")] if _email4 else []),
    *([(_phone4.group(1).strip(), "{{contact}}")] if _phone4 else []),
])

# ── 5 · Modern Landing Page (UiXSHUVO) ──────────────────────────────────────
_p5 = (BASE / "5" / "index.html").read_text(encoding="utf-8", errors="replace")

# Find the brand name inside logo div
_brand5 = re.search(r'>\s*(UiXSHUVO|[A-Z][A-Za-z]{3,})\s*<', _p5)
_brand5_txt = _brand5.group(1).strip() if _brand5 else "UiXSHUVO"

_phone5 = re.search(r'(\+[\d\s\(\)\-]{7,})', _p5)
_email5 = re.search(r'[\w\.\-]+@[\w\.\-]+\.[a-z]{2,}', _p5)
_addr5  = re.search(r'(\d+\s+[A-Za-z ]+(?:Street|Ave|Blvd|Road|Rd|Drive|Lane)[A-Za-z ,\.]*)', _p5)

patch("5", [
    ("<title>Modern Real Estate Landing Page</title>", "<title>{{title}}</title>"),
    (_brand5_txt, "{{title}}"),
    # Footer copyright
    (f"© 2026 {_brand5_txt} Real Estate. All rights reserved.", "© 2026 {{title}}. All rights reserved."),
    (f"© 2025 {_brand5_txt}", "© 2026 {{title}}"),
    (f"© 2024 {_brand5_txt}", "© 2026 {{title}}"),
    *([(_phone5.group(1).strip(), "{{contact}}")] if _phone5 else []),
    *([(_email5.group(0), "{{contact}}")] if _email5 else []),
    *([(_addr5.group(1).strip(), "{{address}}")] if _addr5 else []),
])

# ── r-6 · Homzen ────────────────────────────────────────────────────────────
patch("r-6", [
    ("<title>Homzen - Find Your Dream Home</title>", "<title>{{title}}</title>"),
    (">Homzen<", ">{{title}}<"),
    ("© 2024 Homzen. All rights reserved.", "© 2026 {{title}}. All rights reserved."),
    ("Why Choose Homzen", "Why Choose {{title}}"),
    ("4517 Washington Ave. Manchester, Kentucky 39495", "{{address}}"),
    ("(406) 555-0120", "{{contact}}"),
])

# ── r-7 · Real Estate Find Properties ────────────────────────────────────────
_p7 = (BASE / "r-7" / "index.html").read_text(encoding="utf-8", errors="replace")
_email7 = re.search(r'[\w\.\-]+@[\w\.\-]+\.[a-z]{2,}', _p7)
_phone7 = re.search(r'(\+[\d\s\(\)\-]{7,})', _p7)
_addr7  = re.search(r'(\d+\s+[A-Za-z ]+(?:Street|Ave|Blvd|Road|Rd|Drive|Lane)[A-Za-z ,\.]*)', _p7)
# Find the brand name in the logo
_brand7 = re.search(r'class="logo[^>]*>\s*(?:<[^>]+>)*([A-Z][A-Za-z& ]+)(?:</[^>]+>)*\s*</a>', _p7)
_brand7_txt = _brand7.group(1).strip() if _brand7 else ""

patch("r-7", [
    ("<title>Real Estate - Find Your Properties</title>", "<title>{{title}}</title>"),
    *([(_brand7_txt, "{{title}}")] if _brand7_txt else []),
    *([(_email7.group(0), "{{contact}}")] if _email7 else []),
    *([(_phone7.group(1).strip(), "{{contact}}")] if _phone7 else []),
    *([(_addr7.group(1).strip(), "{{address}}")] if _addr7 else []),
])

# ── r-8 · Archera Interior Studio ────────────────────────────────────────────
patch("r-8", [
    ("<title>Archera Interior Studio</title>", "<title>{{title}}</title>"),
    (">Archera<", ">{{title}}<"),
    ("Archera Interior Studio", "{{title}}"),
    ("hello@archera.studio", "{{contact}}"),
    ("Archera Studio", "{{title}}"),
])

# ── r-10 · Browed ────────────────────────────────────────────────────────────
_p10 = (BASE / "r-10" / "index.html").read_text(encoding="utf-8", errors="replace")
_email10 = re.search(r'[\w\.\-]+@[\w\.\-]+\.[a-z]{2,}', _p10)
_phone10 = re.search(r'(\+[\d\s\(\)\-]{7,})', _p10)
_addr10  = re.search(r'href="contact\.html"[^>]*>\s*Contact\s*</a>\s*</div>\s*</div>\s*</div>\s*</header>', _p10)  # too specific, use generic
_addr10  = re.search(r'(\d+\s+[A-Za-z ]+(?:Street|Ave|Blvd|Road|Rd|Drive|Lane)[A-Za-z ,\.]*)', _p10)

patch("r-10", [
    ("<title>Browed | Exclusive Homes for Premium Buyers</title>", "<title>{{title}} | Real Estate</title>"),
    (">Browed<", ">{{title}}<"),
    ("© 2026 Browed Luxury\n                        Estate. All rights reserved.",
     "© 2026 {{title}}. All rights reserved."),
    ("Comfort and exclusivity await. Step into home financing and viewing immediately with our\n                            dedicated agents.",
     "{{details}}"),
    ("All over the world, finding premium homes has rarely been this easy. Enjoy the\n                        selection carefully crafted on our premium platform.",
     "{{details}}"),
    *([(_email10.group(0), "{{contact}}")] if _email10 else []),
    *([(_phone10.group(1).strip(), "{{contact}}")] if _phone10 else []),
    *([(_addr10.group(1).strip(), "{{address}}")] if _addr10 else []),
])

print("\n✅ All templates patched. Clear generated/ cache and test fresh clients.")
