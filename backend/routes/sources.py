from datetime import date
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend import models
from backend.auth import get_current_user
from backend.database import get_db

router = APIRouter(prefix="/api/sources", tags=["sources"])


# ------------------------------------------------------------------
# Schemas
# ------------------------------------------------------------------

class SourceCreate(BaseModel):
    name: str
    url: str
    social_network: str
    start_date: date
    refresh_rate: str = "never"
    refresh_window: Optional[str] = None


class SourceUpdate(SourceCreate):
    is_active: bool = True


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------

@router.get("")
def list_sources(
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    sources = db.query(models.InformationSource).order_by(models.InformationSource.name).all()
    return [_serialize(s) for s in sources]


@router.post("", status_code=201)
def create_source(
    body: SourceCreate,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    _validate(body)
    handle = _extract_handle(body.url)
    src = models.InformationSource(
        name=body.name,
        url=body.url,
        social_network=body.social_network,
        profile_handle=handle,
        start_date=body.start_date,
        refresh_rate=body.refresh_rate,
        refresh_window=body.refresh_window if body.refresh_rate != "never" else None,
    )
    db.add(src)
    db.commit()
    db.refresh(src)
    return _serialize(src)


@router.get("/{source_id}")
def get_source(
    source_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    src = _get_or_404(db, source_id)
    return _serialize(src)


@router.put("/{source_id}")
def update_source(
    source_id: int,
    body: SourceUpdate,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    src = _get_or_404(db, source_id)
    _validate(body)
    src.name           = body.name
    src.url            = body.url
    src.social_network = body.social_network
    src.profile_handle = _extract_handle(body.url)
    src.start_date     = body.start_date
    src.refresh_rate   = body.refresh_rate
    src.refresh_window = body.refresh_window if body.refresh_rate != "never" else None
    src.is_active      = body.is_active
    db.commit()
    db.refresh(src)
    return _serialize(src)


@router.delete("/{source_id}", status_code=204)
def delete_source(
    source_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    src = _get_or_404(db, source_id)
    db.delete(src)
    db.commit()


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

VALID_NETWORKS  = {"facebook", "instagram", "twitter"}
VALID_RATES     = {"30min", "1h", "4h", "12h", "24h", "never"}
VALID_WINDOWS   = {"24h", "48h", "72h", "1week"}


def _validate(body):
    if body.social_network not in VALID_NETWORKS:
        raise HTTPException(400, f"Red social inválida. Opciones: {VALID_NETWORKS}")
    if body.refresh_rate not in VALID_RATES:
        raise HTTPException(400, f"Tasa de refresco inválida. Opciones: {VALID_RATES}")
    if body.refresh_rate != "never" and body.refresh_window not in VALID_WINDOWS:
        raise HTTPException(400, f"Ventana de refresco requerida. Opciones: {VALID_WINDOWS}")


def _get_or_404(db: Session, source_id: int) -> models.InformationSource:
    src = db.query(models.InformationSource).filter(
        models.InformationSource.id == source_id
    ).first()
    if not src:
        raise HTTPException(404, "Fuente no encontrada.")
    return src


def _extract_handle(url: str) -> str:
    url = url.rstrip("/")
    parts = url.split("/")
    for part in reversed(parts):
        if part and "." not in part:
            return part.lstrip("@")
    return url


def _serialize(s: models.InformationSource) -> dict:
    return {
        "id": s.id,
        "name": s.name,
        "url": s.url,
        "social_network": s.social_network,
        "profile_handle": s.profile_handle,
        "start_date": str(s.start_date),
        "refresh_rate": s.refresh_rate,
        "refresh_window": s.refresh_window,
        "is_active": s.is_active,
        "last_scraped_at": s.last_scraped_at.isoformat() if s.last_scraped_at else None,
        "created_at": s.created_at.isoformat(),
    }
