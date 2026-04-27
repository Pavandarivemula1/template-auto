"""
models.py – SQLAlchemy ORM models.
Phase 3: Added email, location, logo_text columns.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class Client(Base):
    """Stores each client's form submission."""
    __tablename__ = "clients"

    id          = Column(Integer, primary_key=True, index=True)
    title       = Column(String(200), nullable=False)
    contact     = Column(String(200), nullable=False)
    email       = Column(String(200), nullable=True,  default="")
    address     = Column(String(300), nullable=False)
    location    = Column(String(200), nullable=True,  default="")
    details     = Column(String(1000), nullable=False)
    logo_text   = Column(String(200), nullable=True,  default="")
    status      = Column(String(20),  default="Draft")   # Draft / Processing / Ready
    created_at  = Column(DateTime,    default=datetime.utcnow)

    selection = relationship("TemplateSelection", back_populates="client", uselist=False)


class TemplateSelection(Base):
    """Records which template was chosen and the path to generated HTML."""
    __tablename__ = "template_selections"

    id              = Column(Integer, primary_key=True, index=True)
    client_id       = Column(Integer, ForeignKey("clients.id"), unique=True)
    template_name   = Column(String(50),  nullable=False)
    generated_path  = Column(String(300), nullable=True)

    client = relationship("Client", back_populates="selection")
