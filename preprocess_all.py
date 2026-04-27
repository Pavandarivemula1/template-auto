"""
preprocess_all.py  –  CLI Script: Template Preprocessing

Run this ONE TIME after importing new templates.
It converts every raw demo template into a clean {{placeholder}} system.

Usage (from the template_engine/ directory):
    python preprocess_all.py

Options:
    --template NAME   Process only one template (e.g. --template r-8)
    --dry-run         Detect and report but do NOT write changes
    --list            Show all available templates

Example:
    python preprocess_all.py
    python preprocess_all.py --template 2
    python preprocess_all.py --dry-run
"""
import sys
import logging
import argparse
from pathlib import Path

# Make sure the parent package is on the path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import config   # noqa: ensures TEMPLATES_DIR is set
from template_engine.preprocessor import preprocess_template, preprocess_all, KNOWN_DEMO_BRANDS

# ── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("preprocess_cli")


def main():
    parser = argparse.ArgumentParser(
        description="Preprocess raw demo templates into clean {{placeholder}} versions."
    )
    parser.add_argument("--template", metavar="NAME", help="Process only this template folder")
    parser.add_argument("--dry-run", action="store_true", help="Detect only, do NOT write changes")
    parser.add_argument("--list",    action="store_true", help="List available templates and exit")
    args = parser.parse_args()

    from config import TEMPLATES_DIR, VALID_TEMPLATES

    if args.list:
        print("\nAvailable templates:")
        for t in sorted(VALID_TEMPLATES):
            tmpl_dir = TEMPLATES_DIR / t
            has_map = (tmpl_dir / "template_map.json").exists()
            status = "[OK preprocessed]" if has_map else "[raw]"
            html_count = len(list(tmpl_dir.rglob("*.html")))
            print(f"  {t:12}  {html_count:2d} pages   {status}")
        return

    print("\n" + "=" * 60)
    print("  TEMPLATE PREPROCESSING ENGINE")
    print("=" * 60)
    if args.dry_run:
        print("  DRY-RUN MODE: No files will be modified.")
    print()

    if args.template:
        templates_to_process = [args.template]
    else:
        templates_to_process = sorted(VALID_TEMPLATES)

    total_pages = 0
    total_modified = 0
    errors = []

    for tmpl_name in templates_to_process:
        if tmpl_name == "ui":
            continue   # system UI, not a client template
        print(f"  Processing: {tmpl_name}...", end=" ", flush=True)
        report = preprocess_template(tmpl_name, dry_run=args.dry_run)

        if report.ok:
            print(f"OK  {report.pages_modified}/{report.pages_processed} pages modified")
            total_pages += report.pages_processed
            total_modified += report.pages_modified

            if report.detected_emails:
                print(f"       emails found:  {report.detected_emails}")
            if report.detected_phones:
                print(f"       phones found:  {report.detected_phones}")
            if report.mappings:
                unique_originals = {m['original'] for m in report.mappings}
                print(f"       brands/slogans replaced: {len(unique_originals)}")
        else:
            print("FAILED")
            for err in report.errors:
                print(f"       ERROR: {err}")
            errors.extend(report.errors)

    print()
    print("=" * 60)
    print(f"  DONE:  {total_modified}/{total_pages} total pages modified")
    if errors:
        print(f"  {len(errors)} error(s):")
        for err in errors:
            print(f"    - {err}")
    else:
        print("  All templates preprocessed successfully.")
        if not args.dry_run:
            print("  template_map.json saved in each template folder.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
