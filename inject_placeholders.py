"""
inject_placeholders.py  –  One-time script to stamp {{placeholder}} tokens
into each real-estate index.html so the engine can replace them at runtime.

Run once:  python inject_placeholders.py
"""
import re
from pathlib import Path

BASE = Path(__file__).parent / "templates"

# ── Per-template replacement rules ────────────────────────────────────────────
# Each entry:  folder → list of (old_text, new_text)  applied in order.
# We replace exact strings so we don't accidentally corrupt markup.
RULES = {

    # ── 1 – Archetype / Solara ─────────────────────────────────────────────
    "1": [
        ('<title>Archetype | Solara Theme - Visionary Architecture &amp; Design</title>',
         '<title>{{title}} | Real Estate</title>'),
        ('<title>Archetype | Solara Theme - Visionary Architecture & Design</title>',
         '<title>{{title}} | Real Estate</title>'),
        ('>ARCHETYPE<', '>{{title}}<'),
        ('An award-winning architectural design firm specializing in sustainable luxury, bespoke residential retreats, and visionary commercial environments.',
         '{{details}}'),
        ('© 2026 Archetype. All rights reserved.',
         '© 2026 {{title}}. All rights reserved.'),
        ('Sculpting Light, Defining Space. | Guntur, AP',
         '{{address}}'),
        ('wa.me/919876543210', 'tel:{{contact}}'),
        ('content="Archetype"', 'content="{{title}}"'),
        ('content="Archetype | Solara Theme - Sculpting Light, Defining Space"',
         'content="{{title}}"'),
    ],

    # ── 2 – Actura ─────────────────────────────────────────────────────────
    "2": [
        ('<title>Actura - Construction</title>',
         '<title>{{title}}</title>'),
        ('>Actura<', '>{{title}}<'),
        ('Actura', '{{title}}'),          # broad fallback – runs last via ordering
        ('info@actura.com', '{{contact}}'),
        ('+1 (555) 123-4567', '{{contact}}'),
        ('123 Construction Ave, Builder City', '{{address}}'),
    ],

    # ── 3 – Generic Real Estate (Construction Company) ─────────────────────
    "3": [
        ('<title>Real Estate - Construction Company</title>',
         '<title>{{title}}</title>'),
        # Hero description (first prominent <p> after h1)
        ('Comfortable turnkey concrete homes', '{{title}}'),
        ('We build quality homes that last a lifetime.', '{{details}}'),
        ('+1 234 567 890', '{{contact}}'),
        ('123 Main Street, City', '{{address}}'),
    ],

    # ── 4 – Horizon ────────────────────────────────────────────────────────
    "4": [
        ('<title>Horizon | Discover Your Dream Home</title>',
         '<title>{{title}} | Real Estate</title>'),
        ('>Horizon<', '>{{title}}<'),
        ('Horizon', '{{title}}'),
        ('We are a real estate agency that will help you find the best property',
         '{{details}}'),
        ('+1 (800) 555-HORIZON', '{{contact}}'),
        ('100 Dream Street, Home City', '{{address}}'),
    ],

    # ── 5 – Modern Landing Page ────────────────────────────────────────────
    "5": [
        ('<title>Modern Real Estate Landing Page</title>',
         '<title>{{title}}</title>'),
        ('Connecting you to the home you love', '{{title}}'),
        ('We help families find their perfect home with expert guidance and a personal touch.',
         '{{details}}'),
        ('contact@realestate.com', '{{contact}}'),
        ('Downtown Office, Main City', '{{address}}'),
    ],

    # ── r-6 – Homzen ───────────────────────────────────────────────────────
    "r-6": [
        ('<title>Homzen - Find Your Dream Home</title>',
         '<title>{{title}}</title>'),
        ('>Homzen<', '>{{title}}<'),
        ('© 2024 Homzen. All rights reserved.', '© 2026 {{title}}. All rights reserved.'),
        ('4517 Washington Ave. Manchester, Kentucky 39495', '{{address}}'),
        ('(406) 555-0120', '{{contact}}'),
        ('Why Choose Homzen', 'Why Choose {{title}}'),
    ],

    # ── r-7 – Generic Real Estate ──────────────────────────────────────────
    "r-7": [
        ('<title>Real Estate - Find Your Properties</title>',
         '<title>{{title}}</title>'),
        ('Find Your Properties', '{{title}}'),
        ('We are a premier real estate agency.', '{{details}}'),
        ('contact@realestate.com', '{{contact}}'),
        ('City Center, Main Street', '{{address}}'),
    ],

    # ── r-8 – Archera Interior Studio ─────────────────────────────────────
    "r-8": [
        ('<title>Archera Interior Studio</title>',
         '<title>{{title}}</title>'),
        ('>Archera<', '>{{title}}<'),
        ('Archera Interior Studio', '{{title}}'),
        ('The inspired design of tomorrow', '{{details}}'),
        ('hello@archera.studio', '{{contact}}'),
        ('Studio District, Design City', '{{address}}'),
    ],

    # ── r-10 – Browed ──────────────────────────────────────────────────────
    "r-10": [
        ('<title>Browed | Exclusive Homes for Premium Buyers</title>',
         '<title>{{title}} | Real Estate</title>'),
        ('>Browed<', '>{{title}}<'),
        ('© 2026 Browed Luxury\n                        Estate. All rights reserved.',
         '© 2026 {{title}}. All rights reserved.'),
        ('Comfort and exclusivity await. Step into home financing and viewing immediately with our\n                            dedicated agents.',
         '{{details}}'),
        ('All over the world, finding premium homes has rarely been this easy. Enjoy the\n                        selection carefully crafted on our premium platform.',
         '{{details}}'),
    ],
}


def inject(folder: str, rules: list):
    path = BASE / folder / "index.html"
    if not path.exists():
        print(f"[SKIP] {folder}: no index.html")
        return

    html = path.read_text(encoding="utf-8", errors="replace")
    changed = 0
    for old, new in rules:
        if old in html:
            html = html.replace(old, new, 1)
            changed += 1

    path.write_text(html, encoding="utf-8")
    print(f"[OK]   {folder}: {changed}/{len(rules)} replacements applied")


if __name__ == "__main__":
    for folder, rules in RULES.items():
        inject(folder, rules)
    print("\nDone. All templates updated with {{placeholders}}.")
