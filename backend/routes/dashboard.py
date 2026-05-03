from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend import models
from backend.auth import get_current_user
from backend.database import get_db

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("")
def get_dashboard(
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    # ------------------------------------------------------------------
    # KPIs globales
    # ------------------------------------------------------------------
    total_sources  = db.query(func.count(models.InformationSource.id)).scalar() or 0
    total_posts    = db.query(func.count(models.Post.id)).scalar() or 0
    total_comments = db.query(func.count(models.Comment.id)).scalar() or 0

    pos_count = (
        db.query(func.count(models.Comment.id))
        .filter(models.Comment.sentiment == "positive")
        .scalar() or 0
    )
    neg_count = (
        db.query(func.count(models.Comment.id))
        .filter(models.Comment.sentiment == "negative")
        .scalar() or 0
    )
    neu_count = total_comments - pos_count - neg_count

    pos_pct = round(pos_count / total_comments * 100, 1) if total_comments else 0
    neg_pct = round(neg_count / total_comments * 100, 1) if total_comments else 0

    # ------------------------------------------------------------------
    # Config semáforo
    # ------------------------------------------------------------------
    tl = db.query(models.TrafficLightConfig).first()
    green_min  = tl.green_min_pct  if tl else 61.0
    yellow_min = tl.yellow_min_pct if tl else 31.0
    yellow_max = tl.yellow_max_pct if tl else 60.0
    red_max    = tl.red_max_pct    if tl else 30.0

    def traffic_color(pct_pos: float) -> str:
        if pct_pos >= green_min:
            return "green"
        if yellow_min <= pct_pos <= yellow_max:
            return "yellow"
        return "red"

    # ------------------------------------------------------------------
    # Datos por eje (solo activos)
    # ------------------------------------------------------------------
    topics = (
        db.query(models.Topic)
        .filter(models.Topic.is_active == True)
        .order_by(models.Topic.display_order)
        .all()
    )

    semaphore = []
    for topic in topics:
        t_pos = (
            db.query(func.count(models.Comment.id))
            .join(models.Post, models.Post.id == models.Comment.post_id)
            .filter(
                models.Post.topic_id == topic.id,
                models.Comment.sentiment == "positive",
            )
            .scalar() or 0
        )
        t_neg = (
            db.query(func.count(models.Comment.id))
            .join(models.Post, models.Post.id == models.Comment.post_id)
            .filter(
                models.Post.topic_id == topic.id,
                models.Comment.sentiment == "negative",
            )
            .scalar() or 0
        )
        t_total = t_pos + t_neg
        t_pos_pct = round(t_pos / t_total * 100, 1) if t_total else 0
        t_neg_pct = round(t_neg / t_total * 100, 1) if t_total else 0

        semaphore.append({
            "topic_id"  : topic.id,
            "topic_name": topic.name,
            "icon"      : topic.icon,
            "color"     : traffic_color(t_pos_pct),
            "positive"  : t_pos,
            "negative"  : t_neg,
            "total"     : t_total,
            "pos_pct"   : t_pos_pct,
            "neg_pct"   : t_neg_pct,
        })

    return {
        "kpis": {
            "total_sources" : total_sources,
            "total_posts"   : total_posts,
            "total_comments": total_comments,
            "positive"      : pos_count,
            "negative"      : neg_count,
            "neutral"       : neu_count,
            "pos_pct"       : pos_pct,
            "neg_pct"       : neg_pct,
        },
        "semaphore": semaphore,
        "traffic_light_config": {
            "green_min" : green_min,
            "yellow_min": yellow_min,
            "yellow_max": yellow_max,
            "red_max"   : red_max,
        },
    }
