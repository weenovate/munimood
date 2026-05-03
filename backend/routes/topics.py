from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend import models
from backend.auth import get_current_user, require_admin
from backend.database import get_db

router = APIRouter(prefix="/api/topics", tags=["topics"])


class TopicCreate(BaseModel):
    name: str
    icon: str = "bi-circle"
    display_order: int = 0
    is_active: bool = True


@router.get("")
def list_topics(
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    topics = db.query(models.Topic).order_by(models.Topic.display_order).all()
    return [_serialize(t) for t in topics]


@router.post("", status_code=201)
def create_topic(
    body: TopicCreate,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin),
):
    existing = db.query(models.Topic).filter(models.Topic.name == body.name).first()
    if existing:
        raise HTTPException(400, "Ya existe un eje con ese nombre.")
    topic = models.Topic(**body.model_dump())
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return _serialize(topic)


@router.put("/{topic_id}")
def update_topic(
    topic_id: int,
    body: TopicCreate,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin),
):
    topic = _get_or_404(db, topic_id)
    topic.name          = body.name
    topic.icon          = body.icon
    topic.display_order = body.display_order
    topic.is_active     = body.is_active
    db.commit()
    db.refresh(topic)
    return _serialize(topic)


@router.delete("/{topic_id}", status_code=204)
def delete_topic(
    topic_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin),
):
    topic = _get_or_404(db, topic_id)
    db.delete(topic)
    db.commit()


def _get_or_404(db: Session, topic_id: int) -> models.Topic:
    t = db.query(models.Topic).filter(models.Topic.id == topic_id).first()
    if not t:
        raise HTTPException(404, "Eje no encontrado.")
    return t


def _serialize(t: models.Topic) -> dict:
    return {
        "id"           : t.id,
        "name"         : t.name,
        "icon"         : t.icon,
        "display_order": t.display_order,
        "is_active"    : t.is_active,
    }
