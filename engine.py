"""
engine.py – Thin Orchestrator (Phase 4 Modular Architecture)

This file is the public entry point for the entire generation pipeline.
All heavy logic lives in the template_engine/ subpackage:

  template_engine/clone.py     →  clone template folder
  template_engine/analyzer.py  →  lxml DOM structure analysis
  template_engine/detector.py  →  regex detection helpers
  template_engine/injector.py  →  smart content injection
  template_engine/validator.py →  QA scan of generated output

Usage:
    from engine import inject_variables
    index_path = inject_variables(client_id=7, template_name="r-8", client_data={...})
"""
import logging
from pathlib import Path

from template_engine.clone    import clone_template
from template_engine.injector import inject_page, BANNED_BRANDS
from template_engine.validator import validate_site

logger = logging.getLogger("engine")


def inject_variables(client_id: int, template_name: str, client_data: dict) -> str:
    """
    Full generation pipeline for one client.

    Steps:
      1. Validate + clone template folder (clone.py)
      2. For every HTML file: analyze + inject (injector.py)
      3. QA validate generated output (validator.py)

    Args:
        client_id     - unique integer ID from Supabase/DB
        template_name - folder name inside templates/ (e.g. "2", "r-8")
        client_data   - dict: title, contact, email, address,
                        location, details, logo_text

    Returns:
        Absolute string path to the generated index.html

    Raises:
        ValueError        - invalid template name
        FileNotFoundError - template folder or index.html missing
    """
    logger.info("=" * 60)
    logger.info(
        "GENERATION START  client=%s  template=%s  title=%r",
        client_id, template_name, client_data.get("title")
    )
    logger.info(
        "contact=%r  email=%r  address=%r  location=%r",
        client_data.get("contact"), client_data.get("email"),
        client_data.get("address"), client_data.get("location"),
    )

    # Default logo_text to title if not provided
    if not client_data.get("logo_text"):
        client_data = {**client_data, "logo_text": client_data.get("title", "")}

    # ── Step 1: Clone ─────────────────────────────────────────────────────
    out_dir: Path = clone_template(client_id, template_name)

    # ── Step 2: Inject all HTML pages ────────────────────────────────────
    html_files = list(out_dir.rglob("*.html"))
    logger.info("Processing %d HTML pages...", len(html_files))

    modified = 0
    for html_path in html_files:
        try:
            if inject_page(html_path, client_data):
                modified += 1
        except Exception as exc:
            logger.error("[engine] Error processing %s: %s", html_path.name, exc)

    logger.info("Modified %d / %d pages.", modified, len(html_files))

    # ── Step 3: Validate ─────────────────────────────────────────────────
    report = validate_site(out_dir, BANNED_BRANDS)
    if not report.ok:
        for issue in report.issues:
            logger.warning("[engine] Validation issue: %s", issue)

    output_index = out_dir / "index.html"
    logger.info("Output: %s", output_index)
    logger.info("=" * 60)
    return str(output_index)
