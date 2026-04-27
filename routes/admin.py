"""
routes/admin.py  –  Admin API Routes for Template Management

Endpoints:
    GET  /admin/templates              - list all templates + preprocessing status
    POST /admin/preprocess/{name}      - preprocess one template
    POST /admin/preprocess             - preprocess ALL templates
    GET  /admin/template/{name}/map    - view template_map.json for a template

These endpoints are for the developer/admin to run preprocessing after
importing new demo templates. Not exposed to end-clients.
"""
import json
import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from config import TEMPLATES_DIR, VALID_TEMPLATES
from template_engine.preprocessor import preprocess_template, preprocess_all

router = APIRouter(prefix="/admin", tags=["Admin"])
logger = logging.getLogger("routes.admin")


@router.get("/templates")
def list_templates():
    """List all available templates and their preprocessing status."""
    result = []
    for tmpl_name in sorted(VALID_TEMPLATES):
        if tmpl_name == "ui":
            continue
        tmpl_dir = TEMPLATES_DIR / tmpl_name
        map_file = tmpl_dir / "template_map.json"
        html_count = len(list(tmpl_dir.rglob("*.html"))) if tmpl_dir.exists() else 0

        entry = {
            "name": tmpl_name,
            "html_pages": html_count,
            "preprocessed": map_file.exists(),
            "map_path": str(map_file) if map_file.exists() else None,
        }
        if map_file.exists():
            try:
                map_data = json.loads(map_file.read_text(encoding="utf-8"))
                entry["processed_at"] = map_data.get("processed_at")
                entry["pages_modified"] = map_data.get("pages_modified")
                entry["detected_brands"] = map_data.get("detected_brands", [])
            except Exception:
                pass
        result.append(entry)

    return JSONResponse({"templates": result, "total": len(result)})


@router.post("/preprocess/{template_name}")
def preprocess_one(template_name: str, dry_run: bool = False):
    """
    Preprocess a single template: detect demo content and replace
    with {{placeholder}} tokens. Saves template_map.json if not dry_run.
    """
    if template_name not in VALID_TEMPLATES:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown template '{template_name}'. Valid: {sorted(VALID_TEMPLATES)}"
        )

    logger.info("[admin] Preprocessing template: %s  dry_run=%s", template_name, dry_run)
    report = preprocess_template(template_name, dry_run=dry_run)

    return JSONResponse({
        "template_name": template_name,
        "ok": report.ok,
        "dry_run": dry_run,
        "pages_processed": report.pages_processed,
        "pages_modified": report.pages_modified,
        "detected_emails": report.detected_emails,
        "detected_phones": report.detected_phones,
        "mappings": report.mappings,
        "errors": report.errors,
    })


@router.post("/preprocess")
def preprocess_all_templates(dry_run: bool = False):
    """
    Preprocess ALL templates at once.
    Returns a summary for each template.
    """
    logger.info("[admin] Preprocessing ALL templates  dry_run=%s", dry_run)
    reports = preprocess_all(dry_run=dry_run)

    summary = []
    for name, report in reports.items():
        summary.append({
            "template_name": name,
            "ok": report.ok,
            "pages_processed": report.pages_processed,
            "pages_modified": report.pages_modified,
            "detected_brands": report.detected_brands,
            "errors": report.errors,
        })

    total_pages = sum(r["pages_processed"] for r in summary)
    total_modified = sum(r["pages_modified"] for r in summary)

    return JSONResponse({
        "dry_run": dry_run,
        "total_templates": len(summary),
        "total_pages": total_pages,
        "total_modified": total_modified,
        "results": summary,
    })


@router.get("/template/{template_name}/map")
def get_template_map(template_name: str):
    """Return the template_map.json for a preprocessed template."""
    if template_name not in VALID_TEMPLATES:
        raise HTTPException(status_code=400, detail="Unknown template")

    map_file = TEMPLATES_DIR / template_name / "template_map.json"
    if not map_file.exists():
        raise HTTPException(
            status_code=404,
            detail=f"template_map.json not found. Run preprocessing first: POST /admin/preprocess/{template_name}"
        )

    data = json.loads(map_file.read_text(encoding="utf-8"))
    return JSONResponse(data)
