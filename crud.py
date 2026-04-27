"""
crud.py – Database CRUD helper functions.
Phase 3: Handles email, location, logo_text fields.
"""
from sqlalchemy.orm import Session
from models import Client, TemplateSelection
from schemas import ClientCreate, TemplateSelectRequest


# ── Client ────────────────────────────────────────────────────────────────────

def create_client(db: Session, data: ClientCreate) -> Client:
    """Insert a new client record with status=Draft."""
    client = Client(
        title     = data.title,
        contact   = data.contact,
        email     = data.email     or "",
        address   = data.address,
        location  = data.location  or "",
        details   = data.details,
        logo_text = data.logo_text or "",
        status    = "Draft",
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


def get_client(db: Session, client_id: int) -> Client | None:
    """Fetch a single client by primary key."""
    return db.query(Client).filter(Client.id == client_id).first()


def update_client_status(db: Session, client_id: int, status: str) -> Client | None:
    """Update the status field of a client."""
    client = get_client(db, client_id)
    if client:
        client.status = status
        db.commit()
        db.refresh(client)
    return client


# ── Template Selection ─────────────────────────────────────────────────────────

def create_template_selection(
    db: Session,
    client_id: int,
    template_name: str,
    generated_path: str,
) -> TemplateSelection:
    """Insert or update the template selection for a client."""
    existing = get_template_selection(db, client_id)
    if existing:
        existing.template_name  = template_name
        existing.generated_path = generated_path
        db.commit()
        db.refresh(existing)
        return existing

    selection = TemplateSelection(
        client_id=client_id,
        template_name=template_name,
        generated_path=generated_path,
    )
    db.add(selection)
    db.commit()
    db.refresh(selection)
    return selection


def get_template_selection(db: Session, client_id: int) -> TemplateSelection | None:
    """Fetch the template selection for a client."""
    return (
        db.query(TemplateSelection)
        .filter(TemplateSelection.client_id == client_id)
        .first()
    )
