"""
fix_logo.py — Replace the visible logo/navbar brand text with {{title}}
in every real-estate template index.html.

Each template is handled individually with the EXACT string found in the file.
Run: python fix_logo.py
"""
from pathlib import Path
import re

BASE = Path(__file__).parent / "templates"


def fix(folder: str, old: str, new: str = "{{title}}"):
    p = BASE / folder / "index.html"
    html = p.read_text("utf-8", errors="replace")
    if old in html:
        html = html.replace(old, new)
        p.write_text(html, "utf-8")
        print(f"  [OK] [{folder}] replaced: {repr(old[:60])}")
        return True
    else:
        print(f"  [??] [{folder}] NOT FOUND: {repr(old[:60])}")
        return False


print("=== Fixing logo/nav brand text in all templates ===\n")

# ── 1 · Archetype ────────────────────────────────────────────────────────────
# Logo: <a href="#" class="logo" ...>ARCHETYPE</a>
fix("1", ">ARCHETYPE<", ">{{title}}<")

# ── 2 · Actura ───────────────────────────────────────────────────────────────
# Read and find the logo text
_h2 = (BASE / "2" / "index.html").read_text("utf-8", errors="replace")
m = re.search(r'(class="(?:logo|navbar-brand|brand|site-logo)[^"]*"[^>]*>)([\s\S]{0,200}?)(</a>|</div>|</span>)', _h2)
if m:
    inner = m.group(2)
    # find text node inside
    text = re.sub(r'<[^>]+>', '', inner).strip()
    if text and text != "{{title}}":
        fix("2", text, "{{title}}")
    else:
        print(f"  [2] logo inner text: {repr(text)}")
# Also try common patterns
for brand in ["Actura", "ACTURA", "actura"]:
    _h2b = (BASE / "2" / "index.html").read_text("utf-8", errors="replace")
    if f">{brand}<" in _h2b:
        fix("2", f">{brand}<", ">{{title}}<")
        break
    if f'class="logo">{brand}' in _h2b:
        fix("2", f'class="logo">{brand}', 'class="logo">{{title}}')
        break

# ── 3 · Generic Construction ──────────────────────────────────────────────────
_h3 = (BASE / "3" / "index.html").read_text("utf-8", errors="replace")
for pat in [r'<(?:a|div|span)[^>]*class="[^"]*(?:logo|brand)[^"]*"[^>]*>([\s\S]{0,150}?)</(?:a|div|span)>']:
    m3 = re.search(pat, _h3)
    if m3:
        inner3 = re.sub(r'<[^>]+>', '', m3.group(1)).strip()
        if inner3 and inner3 != "{{title}}":
            print(f"  [3] logo text found: {repr(inner3)}")
            fix("3", inner3, "{{title}}")
            break

# ── 4 · Horizon ───────────────────────────────────────────────────────────────
_h4 = (BASE / "4" / "index.html").read_text("utf-8", errors="replace")
# Try >Horizon< pattern
for brand in ["Horizon", "HORIZON"]:
    if f">{brand}<" in _h4:
        fix("4", f">{brand}<", ">{{title}}<"); break

# ── 5 · UiXSHUVO / Modern ──────────────────────────────────────────────────────
_h5 = (BASE / "5" / "index.html").read_text("utf-8", errors="replace")
# The brand UiXSHUVO is inside a span/div near the logo
m5 = re.search(r'(class="logo"[^>]*>[\s\S]{0,300}?<span[^>]*>)(UiXSHUVO|[A-Z][A-Za-z]{2,})(</span>)', _h5)
if m5:
    fix("5", m5.group(2), "{{title}}")
else:
    # Try direct text replacement
    for brand in ["UiXSHUVO"]:
        if brand in _h5 and brand + "<" in _h5:
            fix("5", brand + "<", "{{title}}<")
            break
        elif brand in _h5:
            fix("5", brand, "{{title}}")
            break

# ── r-6 · Homzen ───────────────────────────────────────────────────────────────
fix("r-6", ">Homzen<", ">{{title}}<")

# ── r-7 · Real Estate ──────────────────────────────────────────────────────────
_h7 = (BASE / "r-7" / "index.html").read_text("utf-8", errors="replace")
m7 = re.search(r'(class="(?:logo|navbar-brand|brand|site-logo)[^"]*"[^>]*>)([\s\S]{0,200}?)(</a>|</div>)', _h7)
if m7:
    inner7 = re.sub(r'<[^>]+>', '', m7.group(2)).strip()
    if inner7 and inner7 != "{{title}}":
        fix("r-7", inner7, "{{title}}")

# ── r-8 · Archera ──────────────────────────────────────────────────────────────
_h8 = (BASE / "r-8" / "index.html").read_text("utf-8", errors="replace")
for brand in ["Archera Interior Studio", "Archera"]:
    if f">{brand}<" in _h8:
        fix("r-8", f">{brand}<", ">{{title}}<"); break
    if brand in _h8 and brand != "{{title}}":
        # context-aware: replace inside logo/nav areas only
        logo_match = re.search(r'(class="(?:logo|brand|navbar)[^"]*"[^>]*>[\s\S]{0,200}?)(' + re.escape(brand) + r')([\s\S]{0,50}?</(?:a|div|span)>)', _h8)
        if logo_match:
            fix("r-8", brand, "{{title}}"); break

# ── r-10 · Browed ──────────────────────────────────────────────────────────────
fix("r-10", ">Browed<", ">{{title}}<")

# ── Verify ───────────────────────────────────────────────────────────────────
print("\n=== Final {{title}} check in logo area ===")
for f in ["1","2","3","4","5","r-6","r-7","r-8","r-10"]:
    html = (BASE / f / "index.html").read_text("utf-8", errors="replace")
    total = len(re.findall(r'\{\{title\}\}', html))
    # Check first occurrence context
    m = re.search(r'\{\{title\}\}', html)
    ctx = html[max(0,m.start()-50):m.end()+20].replace('\n',' ').replace('\r','').strip() if m else ''
    print(f"  [{f}] {total}x  first: ...{ctx}...")
