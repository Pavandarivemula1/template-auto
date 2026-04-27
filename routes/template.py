"""
routes/template.py – Template selection and multi-page preview endpoints.

POST /template/select    →  generate full website, set status=Ready
GET  /preview/{id}       →  render preview wrapper page (iframe)
GET  /generated/{id}     →  serve generated index.html (no-cache)
GET  /generated/{id}/{path} → serve any sub-page or asset inside client folder
GET  /download/{id}      →  download generated index.html
"""
import logging
import zipfile
import io
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse, Response, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from config import VALID_TEMPLATES, GENERATED_SITES_DIR
from database import get_db
import crud
from engine import inject_variables
from schemas import TemplateSelectRequest, TemplateSelectionOut

router    = APIRouter()
BASE_DIR  = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates" / "ui"))

logger = logging.getLogger("routes.template")

# Common MIME types for serving assets from generated folders
MIME_MAP = {
    ".html": "text/html; charset=utf-8",
    ".css":  "text/css",
    ".js":   "application/javascript",
    ".png":  "image/png",
    ".jpg":  "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif":  "image/gif",
    ".svg":  "image/svg+xml",
    ".ico":  "image/x-icon",
    ".woff": "font/woff",
    ".woff2":"font/woff2",
    ".ttf":  "font/ttf",
}


# ── POST /template/select ─────────────────────────────────────────────────────

@router.post("/template/select", response_model=TemplateSelectionOut, tags=["Template"])
def select_template(data: TemplateSelectRequest, db: Session = Depends(get_db)):
    """
    Accept {client_id, template_name}, run the full generation pipeline,
    and advance the client status through the lifecycle:

      Processing → Generated → Validated → Ready   (on success)
      Processing → Failed                           (on error)
    """
    logger.info("SELECT  client_id=%s  template=%s", data.client_id, data.template_name)

    client = crud.get_client(db, data.client_id)
    if not client:
        raise HTTPException(status_code=404, detail=f"Client {data.client_id} not found")

    if data.template_name not in VALID_TEMPLATES:
        raise HTTPException(
            status_code=400,
            detail=f"template_name must be one of: {sorted(VALID_TEMPLATES)}"
        )

    logger.info("Client data: title=%r | contact=%r | address=%r | email=%r | location=%r",
                client.title, client.contact, client.address,
                client.email, client.location)

    # ── Status: Processing ────────────────────────────────────────────────
    crud.update_client_status(db, data.client_id, "Processing")

    client_data = {
        "title":     client.title,
        "contact":   client.contact,
        "email":     client.email     or "",
        "address":   client.address,
        "location":  client.location  or "",
        "details":   client.details,
        "logo_text": client.logo_text or client.title,
    }

    try:
        # ── Status: Generated (clone + injection done) ────────────────────
        generated_path = inject_variables(
            client_id=data.client_id,
            template_name=data.template_name,
            client_data=client_data,
        )
        crud.update_client_status(db, data.client_id, "Generated")
        logger.info("Generated path: %s", generated_path)

        # ── Status: Validated ─────────────────────────────────────────────
        # Validation already runs inside inject_variables (validator.py).
        # We promote to Validated here after a successful return.
        crud.update_client_status(db, data.client_id, "Validated")

    except (FileNotFoundError, ValueError) as exc:
        logger.error("Generation failed: %s", exc)
        crud.update_client_status(db, data.client_id, "Failed")
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        logger.error("Unexpected generation error: %s", exc)
        crud.update_client_status(db, data.client_id, "Failed")
        raise HTTPException(status_code=500, detail=f"Generation error: {exc}")

    selection = crud.create_template_selection(
        db,
        client_id=data.client_id,
        template_name=data.template_name,
        generated_path=generated_path,
    )

    # ── Status: Ready ─────────────────────────────────────────────────────
    crud.update_client_status(db, data.client_id, "Ready")
    logger.info("Selection saved id=%s | status=Ready", selection.id)
    return selection



# ── GET /select/{client_id} ──────────────────────────────────────────────────

TEMPLATE_LABELS = {
    "1":    "Template 1 — Classic",
    "2":    "Template 2 — Modern",
    "3":    "Template 3 — Bold",
    "4":    "Template 4 — Horizon Dream",
    "5":    "Template 5 — Minimal",
    "r-6":  "r-6 — Real Estate A",
    "r-7":  "r-7 — Real Estate B",
    "r-8":  "r-8 — Interior Studio",
    "r-9":  "r-9 — Furniture",
    "r-10": "r-10 — Premium Buyers",
}

@router.get("/select/{client_id}", response_class=HTMLResponse, tags=["Template"])
def select_template_page(
    client_id: int,
    request:   Request,
    lead_id:   str = "",
    db:        Session = Depends(get_db),
):
    """
    Full-page visual template selector for a specific client.
    Displays all templates with iframe previews and a "Generate" button each.
    """
    client = crud.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=404, detail=f"Client {client_id} not found")

    tmpl_list = [
        {"id": tid, "label": label}
        for tid, label in TEMPLATE_LABELS.items()
    ]

    return templates.TemplateResponse(request, "select.html", {
        "client":    client,
        "templates": tmpl_list,
        "lead_id":   lead_id,
    })


# ── GET /template/preview/{template_name} ────────────────────────────────────

@router.get("/template/preview/{template_name}", response_class=HTMLResponse, tags=["Template"])
def template_preview(template_name: str):
    """Serve the raw template index.html for visual preview in an iframe."""
    if template_name not in VALID_TEMPLATES:
        raise HTTPException(status_code=404, detail=f"Unknown template: {template_name}")

    tmpl_dir   = BASE_DIR / "templates" / template_name
    index_file = tmpl_dir / "index.html"

    if not index_file.exists():
        raise HTTPException(status_code=404, detail="Template index.html not found")

    html = index_file.read_text(encoding="utf-8", errors="replace")

    # Rewrite relative asset paths so the iframe can load CSS/images
    # e.g. href="style.css" → href="/template/preview/{name}/assets/style.css"
    base_tag = f'<base href="/template/preview/{template_name}/assets/">'
    html = html.replace("<head>", f"<head>{base_tag}", 1)

    return HTMLResponse(content=html)


@router.get("/template/preview/{template_name}/assets/{path:path}", tags=["Template"])
def template_preview_asset(template_name: str, path: str):
    """Serve static assets (CSS, JS, images) for the template preview iframe."""
    if template_name not in VALID_TEMPLATES:
        raise HTTPException(status_code=404, detail="Unknown template")

    asset_path = BASE_DIR / "templates" / template_name / path
    if not asset_path.exists() or not asset_path.is_file():
        raise HTTPException(status_code=404, detail="Asset not found")

    suffix   = asset_path.suffix.lower()
    mime     = MIME_MAP.get(suffix, "application/octet-stream")
    return Response(content=asset_path.read_bytes(), media_type=mime)


# ── GET /preview/{client_id} ──────────────────────────────────────────────────

@router.get("/preview/{client_id}", response_class=HTMLResponse, tags=["Preview"])
def preview_page(client_id: int, request: Request, db: Session = Depends(get_db)):
    """Render the preview wrapper page; iframe loads /generated/{id}."""
    client    = crud.get_client(db, client_id)
    selection = crud.get_template_selection(db, client_id)

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    if not selection or not selection.generated_path:
        raise HTTPException(status_code=404,
                            detail="No website generated yet. Please select a template first.")

    generated_index = Path(selection.generated_path)
    if not generated_index.exists():
        raise HTTPException(status_code=500, detail="Generated file missing from disk.")

    response = templates.TemplateResponse(request, "preview.html", {
        "client":        client,
        "template_name": selection.template_name,
        # Cache-buster: unique per selection
        "preview_src":   f"/generated/{client_id}?v={selection.id}",
    })
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    return response


# ── GET /generated/{client_id} ────────────────────────────────────────────────

@router.get("/generated/{client_id}", response_class=HTMLResponse, tags=["Preview"])
def serve_generated_index(client_id: int, db: Session = Depends(get_db)):
    """
    Serve the generated index.html inside the iframe.
    Uses a base-href so relative links to CSS / JS / other pages resolve correctly.
    """
    selection = crud.get_template_selection(db, client_id)
    if not selection or not selection.generated_path:
        raise HTTPException(status_code=404, detail="Generated page not found")

    generated_index = Path(selection.generated_path)
    if not generated_index.exists():
        raise HTTPException(status_code=500, detail="File missing on disk")

    html = generated_index.read_text(encoding="utf-8")

    # Inject a <base href> so all relative asset links resolve to the client's folder.
    # This is the key to making CSS/JS/images load correctly from an iframe.
    base_tag = f'<base href="/site/{client_id}/">'
    if "<head>" in html:
        html = html.replace("<head>", f"<head>\n    {base_tag}", 1)
    elif "<HEAD>" in html:
        html = html.replace("<HEAD>", f"<HEAD>\n    {base_tag}", 1)

    return HTMLResponse(
        content=html,
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate",
            "Pragma":        "no-cache",
        }
    )


# ── GET /site/{client_id}/{path} ──────────────────────────────────────────────

@router.get("/site/{client_id}/{file_path:path}", tags=["Preview"])
def serve_generated_asset(client_id: int, file_path: str):
    """
    Serve any file (CSS, JS, image, sub-page HTML) from the client's generated folder.
    This enables the base-href approach to work: the iframe can load all assets.
    """
    client_dir  = GENERATED_SITES_DIR / f"client_{client_id}"
    target_file = client_dir / file_path

    # Security: prevent directory traversal
    if not str(target_file.resolve()).startswith(str(client_dir.resolve())):
        raise HTTPException(status_code=403, detail="Access denied")

    if not target_file.exists() or not target_file.is_file():
        raise HTTPException(status_code=404, detail=f"Asset not found: {file_path}")

    suffix   = target_file.suffix.lower()
    media    = MIME_MAP.get(suffix, "application/octet-stream")
    no_cache = {"Cache-Control": "no-store, no-cache, must-revalidate"}

    if suffix == ".html":
        # Do not inject base_tag here. Browsers handle native relative resolution inside sub-directories.
        html = target_file.read_text(encoding="utf-8")
        return HTMLResponse(content=html, headers=no_cache)

    return FileResponse(path=str(target_file), media_type=media)


# ── GET /download/{client_id} ─────────────────────────────────────────────────

@router.get("/download/{client_id}", tags=["Preview"])
def download_generated(client_id: int, db: Session = Depends(get_db)):
    """
    Download the entire generated website as a ZIP file.
    The ZIP contains all pages, CSS, JS and images ready to deploy anywhere.
    """
    selection = crud.get_template_selection(db, client_id)
    if not selection or not selection.generated_path:
        raise HTTPException(status_code=404, detail="Generated page not found")

    client_dir = GENERATED_SITES_DIR / f"client_{client_id}"
    if not client_dir.exists():
        raise HTTPException(status_code=500, detail="Generated folder missing on disk")

    # Build ZIP in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in client_dir.rglob("*"):
            if file_path.is_file():
                arcname = file_path.relative_to(client_dir)
                zf.write(file_path, arcname)

    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename=website_client_{client_id}.zip"
        }
    )
