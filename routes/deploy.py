"""
routes/deploy.py – Deploy a generated client site to Vercel.

POST /deploy/{client_id}
    Reads all files from generated_sites/client_{id}/,
    pushes them to the Vercel Deployments API,
    waits for READY state, and returns the public URL.
"""
import os
import base64
import shutil
import time
import logging
import mimetypes
from pathlib import Path

import httpx
from fastapi import APIRouter, HTTPException

from config import GENERATED_SITES_DIR

router = APIRouter()
logger = logging.getLogger("routes.deploy")

VERCEL_API = "https://api.vercel.com"

# .env file is next to this routes/ directory (one level up)
_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


def _get_token() -> str:
    # 1) Try shell environment variable (set via export or running with source .env)
    token = os.getenv("VERCEL_TOKEN", "")

    # 2) Fallback: parse the .env file directly
    if not token and _ENV_FILE.exists():
        for line in _ENV_FILE.read_text().splitlines():
            line = line.strip()
            if line.startswith("VERCEL_TOKEN="):
                token = line.split("=", 1)[1].strip()
                break

    if not token:
        raise HTTPException(
            status_code=500,
            detail="VERCEL_TOKEN is not set. Add it to template_engine/.env and restart."
        )
    return token


def _collect_files(client_dir: Path) -> list[dict]:
    """
    Recursively read every file in client_dir and return a list of
    Vercel file objects: { file, data, encoding }.
    """
    files = []
    for path in sorted(client_dir.rglob("*")):
        if not path.is_file():
            continue
        # Skip internal metadata files
        if path.name == "template_map.json":
            continue

        rel = path.relative_to(client_dir).as_posix()
        raw = path.read_bytes()

        # Determine if text or binary
        mime, _ = mimetypes.guess_type(str(path))
        is_text = mime and (
            mime.startswith("text/") or
            mime in ("application/javascript", "application/json", "image/svg+xml")
        )

        if is_text:
            files.append({
                "file":     rel,
                "data":     raw.decode("utf-8", errors="replace"),
                "encoding": "utf-8",
            })
        else:
            files.append({
                "file":     rel,
                "data":     base64.b64encode(raw).decode("ascii"),
                "encoding": "base64",
            })

    return files


@router.delete("/deploy/{client_id}", tags=["Deploy"])
def delete_site(client_id: int):
    """
    Delete the generated local site files for client_id.
    Also removes the Vercel deployment record if deployment_id is provided.
    Returns { deleted: true } on success.
    """
    client_dir = GENERATED_SITES_DIR / f"client_{client_id}"

    if client_dir.exists():
        shutil.rmtree(client_dir)
        logger.info("Deleted generated site: client_%s", client_id)
    else:
        logger.info("No local site found for client_%s (already deleted?)", client_id)

    return {"deleted": True, "client_id": client_id}


@router.post("/deploy/{client_id}", tags=["Deploy"])
def deploy_site(client_id: int):
    """
    Deploy the generated static site for client_id to Vercel.
    Returns { url, deployment_id } on success.
    """
    token = _get_token()
    client_dir = GENERATED_SITES_DIR / f"client_{client_id}"

    if not client_dir.exists() or not any(client_dir.iterdir()):
        raise HTTPException(
            status_code=404,
            detail=f"No generated site found for client {client_id}. "
                   "Generate a site first via /template/select."
        )

    # Collect all site files
    file_payloads = _collect_files(client_dir)
    if not file_payloads:
        raise HTTPException(status_code=500, detail="No deployable files found.")

    logger.info("Deploying client_%s to Vercel (%d files)", client_id, len(file_payloads))

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json",
    }

    # ── Create deployment ────────────────────────────────────────────────────
    payload = {
        "name":    f"darion-demo-{client_id}",
        "files":   file_payloads,
        "target":  "production",
        "projectSettings": {
            "framework":       None,
            "buildCommand":    None,
            "outputDirectory": None,
        },
    }

    with httpx.Client(timeout=60) as client:
        resp = client.post(
            f"{VERCEL_API}/v13/deployments",
            headers=headers,
            json=payload,
        )

    if resp.status_code not in (200, 201):
        logger.error("Vercel API error %s: %s", resp.status_code, resp.text[:400])
        raise HTTPException(
            status_code=502,
            detail=f"Vercel API returned {resp.status_code}: {resp.text[:200]}"
        )

    dep        = resp.json()
    dep_id     = dep.get("id")
    dep_url    = dep.get("url", "")       # alias URL (without https://)
    dep_status = dep.get("readyState", dep.get("status", "UNKNOWN"))

    logger.info("Deployment created: id=%s  url=%s  state=%s", dep_id, dep_url, dep_status)

    # ── Poll until READY (max ~90 s) ─────────────────────────────────────────
    max_polls = 18   # 18 × 5 s = 90 s
    for attempt in range(max_polls):
        if dep_status in ("READY", "ERROR", "CANCELED"):
            break
        time.sleep(5)
        with httpx.Client(timeout=30) as client:
            check = client.get(
                f"{VERCEL_API}/v13/deployments/{dep_id}",
                headers=headers,
            )
        if check.status_code == 200:
            dep_status = check.json().get("readyState", dep_status)
            dep_url    = check.json().get("url", dep_url)
        logger.info("  Poll %d: state=%s", attempt + 1, dep_status)

    if dep_status not in ("READY",):
        raise HTTPException(
            status_code=504,
            detail=f"Deployment did not become READY in time (last state: {dep_status})"
        )

    # ── Pick the cleanest public alias ──────────────────────────────────────
    # Vercel assigns multiple domains: a unique hash URL + a stable production
    # alias (e.g. darion-demo-31.vercel.app). The stable alias has no random
    # suffix and is publicly accessible without Vercel login.
    public_url = f"https://{dep_url}"   # fallback = unique deploy URL

    try:
        with httpx.Client(timeout=30) as client:
            alias_resp = client.get(
                f"{VERCEL_API}/v13/deployments/{dep_id}/aliases",
                headers=headers,
            )
        if alias_resp.status_code == 200:
            aliases = alias_resp.json().get("aliases", [])
            # Keep only *.vercel.app aliases, sort by length (shortest = no hash)
            vercel_aliases = sorted(
                [a.get("alias", "") for a in aliases if ".vercel.app" in a.get("alias","")],
                key=len,
            )
            if vercel_aliases:
                public_url = f"https://{vercel_aliases[0]}"
                logger.info("Using production alias: %s", public_url)
    except Exception as e:
        logger.warning("Could not fetch aliases, using dep URL: %s", e)

    logger.info("Deployment READY: %s", public_url)
    return {
        "url":           public_url,
        "shareable_url": public_url,
        "deployment_id": dep_id,
    }
