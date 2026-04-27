"""
template_engine/__init__.py

Exposes the public API of the modular template engine.
Import from here instead of directly from submodules.

Usage:
    from template_engine import process_template
"""

from .clone       import clone_template
from .analyzer    import analyze_page
from .detector    import detect_phones, detect_emails, detect_brands, detect_placeholders
from .injector    import inject_page
from .validator   import validate_site
from .preprocessor import preprocess_template, preprocess_all

__all__ = [
    "clone_template",
    "analyze_page",
    "detect_phones",
    "detect_emails",
    "detect_brands",
    "detect_placeholders",
    "inject_page",
    "validate_site",
    "preprocess_template",
    "preprocess_all",
]
