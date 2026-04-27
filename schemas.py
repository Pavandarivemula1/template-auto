"""
schemas.py – Pydantic models for request validation and response serialization.
Phase 3: Added email, location, logo_text fields.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ── Client ─────────────────────────────────────────────────────────────────────

class ClientCreate(BaseModel):
    title:     str            = Field(..., min_length=1, max_length=200,  example="Harsha Builders")
    contact:   str            = Field(..., min_length=1, max_length=200,  example="+91 98765 43210")
    email:     Optional[str]  = Field("",  max_length=200,                example="info@harshabuilders.com")
    address:   str            = Field(..., min_length=1, max_length=300,  example="12 MG Road, Nellore, AP")
    location:  Optional[str]  = Field("",  max_length=200,                example="Nellore, Andhra Pradesh")
    details:   str            = Field(..., min_length=1, max_length=1000, example="Premium family homes since 2010.")
    logo_text: Optional[str]  = Field("",  max_length=200,                example="HB")


class ClientOut(BaseModel):
    id:         int
    title:      str
    contact:    str
    email:      Optional[str]  = ""
    address:    str
    location:   Optional[str]  = ""
    details:    str
    logo_text:  Optional[str]  = ""
    status:     str
    created_at: datetime

    class Config:
        from_attributes = True


# ── Template Selection ──────────────────────────────────────────────────────────

class TemplateSelectRequest(BaseModel):
    client_id:     int = Field(..., example=1)
    template_name: str = Field(..., example="r-6")


class TemplateSelectionOut(BaseModel):
    id:             int
    client_id:      int
    template_name:  str
    generated_path: Optional[str] = None

    class Config:
        from_attributes = True


# ── Preview ────────────────────────────────────────────────────────────────────

class PreviewOut(BaseModel):
    client_id:      int
    template_name:  str
    status:         str
    generated_path: str
