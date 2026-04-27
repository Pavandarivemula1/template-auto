"""
tests/test_engine.py – Full validation tests (Phase 3).
Tests: 7-field injection, demo data removal, multi-page, cross-client isolation.

Run:
    cd c:\\Users\\Harsha\\Documents\\engine\\template_engine
    python -m pytest tests/test_engine.py -v
"""
import sys, re
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine import inject_variables
from config import GENERATED_SITES_DIR, DEMO_DATA_MAP

# ── Test Clients ──────────────────────────────────────────────────────────────

CLIENT_A = {
    "id": 901, "template": "1",
    "data": {
        "title": "Harsha Builders", "contact": "+91 9000011111",
        "email": "info@harshabuilders.com", "address": "12 MG Road, Nellore",
        "location": "Nellore, AP", "details": "Premium family homes since 2010",
        "logo_text": "HB",
    },
}
CLIENT_B = {
    "id": 902, "template": "r-6",
    "data": {
        "title": "Sunrise Properties", "contact": "+91 8888877777",
        "email": "hello@sunriseprops.com", "address": "Vijayawada, AP",
        "location": "Vijayawada", "details": "Premier real estate across AP",
        "logo_text": "SP",
    },
}
CLIENT_C = {
    "id": 903, "template": "3",
    "data": {
        "title": "Coastal Constructions", "contact": "+91 7777766666",
        "email": "contact@coastal.com", "address": "Durga Layout, Nellore",
        "location": "Nellore, AP", "details": "Building your dream home",
        "logo_text": "CC",
    },
}
CLIENT_D = {
    "id": 904, "template": "r-8",
    "data": {
        "title": "Stylecraft Interiors", "contact": "+91 6666655555",
        "email": "hello@stylecraft.in", "address": "40 Park Road, Hyderabad",
        "location": "Hyderabad, TS", "details": "Award-winning interior studio",
        "logo_text": "SI",
    },
}


def read_all(client_id: int) -> str:
    d = GENERATED_SITES_DIR / f"client_{client_id}"
    return "\n".join(
        f.read_text(encoding="utf-8", errors="replace") for f in d.rglob("*.html")
    )

def do_inject(client: dict) -> str:
    inject_variables(client["id"], client["template"], client["data"])
    return read_all(client["id"])


# ── Tests A: Template 1 ───────────────────────────────────────────────────────

class TestClientA:
    def setup_method(self): self.html = do_inject(CLIENT_A)
    def test_multiple_pages(self):
        d = GENERATED_SITES_DIR / f"client_{CLIENT_A['id']}"
        assert len(list(d.rglob("*.html"))) > 1
    def test_title(self):   assert CLIENT_A["data"]["title"]   in self.html
    def test_contact(self): assert CLIENT_A["data"]["contact"] in self.html
    def test_email(self):   assert CLIENT_A["data"]["email"]   in self.html
    def test_address(self): assert CLIENT_A["data"]["address"] in self.html
    def test_location(self):assert CLIENT_A["data"]["location"]in self.html
    def test_logo_text(self):assert CLIENT_A["data"]["logo_text"] in self.html
    def test_no_tokens(self):
        assert not set(re.findall(r'\{\{[^}]+\}\}', self.html))
    def test_demo_brand_gone(self):
        for brand in DEMO_DATA_MAP.get(CLIENT_A["template"], {}):
            assert brand not in self.html


# ── Tests B: Template r-6 (Homzen) ───────────────────────────────────────────

class TestClientB:
    def setup_method(self): self.html = do_inject(CLIENT_B)
    def test_title(self):   assert CLIENT_B["data"]["title"]   in self.html
    def test_email(self):   assert CLIENT_B["data"]["email"]   in self.html
    def test_no_tokens(self):
        assert not set(re.findall(r'\{\{[^}]+\}\}', self.html))
    def test_homzen_gone(self):
        assert "Homzen" not in self.html
    def test_demo_phone_gone(self):
        assert "(406) 555-0120" not in self.html
    def test_demo_email_gone(self):
        assert "support@homzen.com" not in self.html


# ── Tests C: Template 3 (Darion Homes) ───────────────────────────────────────

class TestClientC:
    def setup_method(self): self.html = do_inject(CLIENT_C)
    def test_multiple_pages(self):
        d = GENERATED_SITES_DIR / f"client_{CLIENT_C['id']}"
        assert len(list(d.rglob("*.html"))) > 1
    def test_title(self):   assert CLIENT_C["data"]["title"]   in self.html
    def test_contact(self): assert CLIENT_C["data"]["contact"] in self.html
    def test_email(self):   assert CLIENT_C["data"]["email"]   in self.html
    def test_darion_homes_gone(self):
        assert "Darion Homes" not in self.html
    def test_demo_phone_gone(self):
        assert "+1 (555) 123-4567" not in self.html
    def test_builder_avenue_gone(self):
        assert "Builder Avenue" not in self.html
    def test_no_tokens(self):
        assert not set(re.findall(r'\{\{[^}]+\}\}', self.html))


# ── Tests D: Template r-8 (ARCHERA) ──────────────────────────────────────────

class TestClientD:
    def setup_method(self): self.html = do_inject(CLIENT_D)
    def test_title(self):   assert CLIENT_D["data"]["title"]   in self.html
    def test_email(self):   assert CLIENT_D["data"]["email"]   in self.html
    def test_archera_gone(self):
        assert "ARCHERA" not in self.html
    def test_demo_email_gone(self):
        assert "info@archera.studio" not in self.html
    def test_interior_st_gone(self):
        assert "Interior St" not in self.html


# ── Cross-Client Isolation ────────────────────────────────────────────────────

class TestIsolation:
    def setup_method(self):
        for c in [CLIENT_A, CLIENT_B, CLIENT_C, CLIENT_D]:
            do_inject(c)
        self.html_a = read_all(CLIENT_A["id"])
        self.html_b = read_all(CLIENT_B["id"])
    def test_a_not_in_b(self):
        assert CLIENT_A["data"]["title"] not in self.html_b
    def test_b_not_in_a(self):
        assert CLIENT_B["data"]["title"] not in self.html_a
    def test_email_isolated(self):
        assert CLIENT_A["data"]["email"] not in self.html_b
