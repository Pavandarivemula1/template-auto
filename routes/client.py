"""
routes/client.py – Client-related API endpoints.

POST /client/create  →  save client data, return id + status
GET  /client/{id}    →  fetch client record
GET  /               →  serve the intake form
GET  /select/{id}    →  serve the template selection page
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pathlib import Path

from database import get_db
import crud
from schemas import ClientCreate, ClientOut

router     = APIRouter()
BASE_DIR   = Path(__file__).resolve().parent.parent
templates  = Jinja2Templates(directory=str(BASE_DIR / "templates" / "ui"))


# ── Pages ──────────────────────────────────────────────────────────────────────

@router.get("/", response_class=HTMLResponse, tags=["Pages"])
def intake_form(request: Request):
    """Serve the client intake HTML form."""
    return templates.TemplateResponse(request, "index.html")


@router.get("/select/{client_id}", response_class=HTMLResponse, tags=["Pages"])
def template_selection_page(client_id: int, request: Request, db: Session = Depends(get_db)):
    """Serve the template selection page for a given client."""
    client = crud.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return templates.TemplateResponse(
        request,
        "select_template.html",
        {"client_id": client_id, "client_name": client.title},
    )


# ── API ────────────────────────────────────────────────────────────────────────

@router.post("/client/create", response_model=ClientOut, tags=["Client"])
def create_client(data: ClientCreate, db: Session = Depends(get_db)):
    """
    Create a new client from form data.
    Returns the saved client record (status = Draft).
    """
    client = crud.create_client(db, data)
    return client


@router.get("/client/{client_id}", response_model=ClientOut, tags=["Client"])
def get_client(client_id: int, db: Session = Depends(get_db)):
    """Fetch a single client record by ID."""
    client = crud.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=404, detail=f"Client {client_id} not found")
    return client
