"""
config.py – Single source of truth for all engine constants.

Phase 3: Added email, location, logo_text to PLACEHOLDER_KEYS.
         Added DEMO_DATA_MAP with per-template hardcoded demo values.
"""
from pathlib import Path

# ── Directories ────────────────────────────────────────────────────────────────
BASE_DIR            = Path(__file__).resolve().parent
TEMPLATES_DIR       = BASE_DIR / "templates"
GENERATED_SITES_DIR = BASE_DIR / "generated_sites"

# ── Template Registry ──────────────────────────────────────────────────────────
VALID_TEMPLATES: set[str] = {
    "1", "2", "3", "4", "5",
    "r-6", "r-7", "r-8", "r-9", "r-10",
}

# ── Placeholder Keys (injected into every HTML file) ──────────────────────────
# These are the ONLY tokens that templates use.
# Engine replaces {{key}} with the real client value.
PLACEHOLDER_KEYS: list[str] = [
    "title",
    "contact",
    "email",
    "address",
    "location",
    "details",
    "logo_text",
]

# ── Per-Template Demo Data Map ─────────────────────────────────────────────────
# Maps each template's hardcoded demo strings → the placeholder that should
# replace them.  Processed in order: brand names first, then contact data.
#
# Format:
#   "template_folder": {
#       "demo string to find": "{{placeholder}}",
#       ...
#   }
#
DEMO_DATA_MAP: dict[str, dict[str, str]] = {

    "1": {
        # Brand names
        "Archetype · Solara": "{{title}}",
        "Archetype Solara":   "{{title}}",
        "Archetype":          "{{title}}",
    },

    "2": {
        # Brand names
        "Actura · Construction": "{{title}}",
        "Actura":                "{{title}}",
        # Demo contact data found in template 2
        "sales@example.com":  "{{email}}",
        "info@example.com":   "{{email}}",
        "+1 234 567 89":      "{{contact}}",
        "+1 987 654 32":      "{{contact}}",
    },

    "3": {
        # Brand names across all 15 pages
        "Darion Homes": "{{title}}",
        # Demo phone numbers
        "+1 (555) 123-4567":  "{{contact}}",
        "+1 (555) 000-0000":  "{{contact}}",
        "+1 (555) 987-6543":  "{{contact}}",
        # Demo email
        "info@darionhomes.com": "{{email}}",
        "hello@darion.com":     "{{email}}",
        # Demo address keyword
        "123 Builder Avenue":   "{{address}}",
        "Builder Avenue":       "{{address}}",
    },

    "4": {
        "Horizon Dream Home": "{{title}}",
        "Horizon":            "{{title}}",
        "Main St":            "{{address}}",
    },

    "5": {
        "Modern Landing Page":      "{{title}}",
        # Demo contact data
        "(555) 000-0000":           "{{contact}}",
        "hello@realestate.com":     "{{email}}",
        "jobs@realestate.com":      "{{email}}",
        "john@example.com":         "{{email}}",
        "jane@realestate.example.com": "{{email}}",
        "Main St":                  "{{address}}",
    },

    "r-6": {
        "Homzen · Find Your Home": "{{title}}",
        "Homzen":                  "{{title}}",
        # Demo contacts
        "(406) 555-0120":          "{{contact}}",
        "+1 (406) 555-0120":       "{{contact}}",
        "support@homzen.com":      "{{email}}",
    },

    "r-7": {
        "Properties & Listings": "{{title}}",
        # Demo contacts
        "+080 1819 427 078":     "{{contact}}",
        "+080181942707":         "{{contact}}",
        "info@realestate.com":   "{{email}}",
    },

    "r-8": {
        "Archera · Interior Studio": "{{title}}",
        "ARCHERA · INTERIOR STUDIO": "{{title}}",
        "ARCHERA":                   "{{title}}",
        # Demo contact
        "info@archera.studio":       "{{email}}",
        # Partial-address prefix bug (already fixed in template, kept as safety net)
        "123 Interior St, New":      "{{address}}",
        "Interior St":               "{{address}}",
        "Main St":                   "{{address}}",
    },

    "r-10": {
        "Browed · Premium Buyers": "{{title}}",
        "Browed":                  "{{title}}",
        "your@email.com":          "{{email}}",
    },

    "r-9": {
        # Compatto furniture / interior template
        "Compatto":              "{{title}}",
        "compatto@furniture.com": "{{email}}",
    },
}
