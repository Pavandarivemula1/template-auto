"""
template_engine/clone.py  –  MODULE A: Template Cloner

Responsibility: Copy the entire source template folder to an isolated
per-client output directory. Never touches the original template.

Usage:
    from template_engine.clone import clone_template
    out_dir = clone_template(client_id=7, template_name="r-8")
"""
import shutil
import logging
from pathlib import Path

from config import TEMPLATES_DIR, GENERATED_SITES_DIR, VALID_TEMPLATES

logger = logging.getLogger("engine.clone")


def clone_template(client_id: int, template_name: str) -> Path:
    """
    Validate the template, then clone its entire folder tree
    (HTML, CSS, JS, images, fonts, assets) to:
        generated_sites/client_{client_id}/

    Args:
        client_id     - Unique integer ID from Supabase/DB
        template_name - Folder name under templates/ (e.g. "2", "r-8")

    Returns:
        Path  pointing to the cloned output directory

    Raises:
        ValueError       - invalid template name
        FileNotFoundError - template folder or index.html missing
    """
    # ── 1. Validate template name ─────────────────────────────────────────
    if template_name not in VALID_TEMPLATES:
        raise ValueError(
            f"Unknown template '{template_name}'. "
            f"Valid choices: {sorted(VALID_TEMPLATES)}"
        )

    src_dir = TEMPLATES_DIR / template_name
    if not src_dir.is_dir():
        raise FileNotFoundError(f"Template folder missing: {src_dir}")
    if not (src_dir / "index.html").exists():
        raise FileNotFoundError(f"index.html not found in template: {src_dir}")

    # ── 2. Prepare output directory ───────────────────────────────────────
    out_dir = GENERATED_SITES_DIR / f"client_{client_id}"

    # Always start fresh so stale pages from a previous template never bleed in
    if out_dir.exists():
        shutil.rmtree(out_dir)
        logger.info("[clone] Removed stale output: %s", out_dir)

    # ── 3. Copy full template tree ────────────────────────────────────────
    shutil.copytree(str(src_dir), str(out_dir))

    # Count what was copied for log clarity
    html_count  = len(list(out_dir.rglob("*.html")))
    asset_count = len(list(out_dir.rglob("*"))) - html_count

    logger.info(
        "[clone] template=%s → client_%s  (%d HTML pages, %d other assets)",
        template_name, client_id, html_count, asset_count
    )

    return out_dir
