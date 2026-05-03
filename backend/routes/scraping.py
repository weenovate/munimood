"""
Endpoints para disparar y monitorear el proceso de scraping.
"""
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend import models
from backend.auth import get_current_user
from backend.database import get_db, SessionLocal
from backend.scrapers.instagram_scraper import InstagramScraper
from backend.scrapers.facebook_scraper   import FacebookScraper
from backend.scrapers.twitter_scraper    import TwitterScraper
from backend.sentiment.analyzer          import analyze_sentiment, classify_topic

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/scraping", tags=["scraping"])


class ScrapeRequest(BaseModel):
    source_id: Optional[int] = None  # None = todas las fuentes activas


@router.post("/trigger")
def trigger_scraping(
    body: ScrapeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    if body.source_id:
        source = db.query(models.InformationSource).filter(
            models.InformationSource.id == body.source_id
        ).first()
        if not source:
            raise HTTPException(404, "Fuente no encontrada.")
        sources = [source]
    else:
        sources = (
            db.query(models.InformationSource)
            .filter(models.InformationSource.is_active == True)
            .all()
        )

    source_ids = [s.id for s in sources]
    background_tasks.add_task(_run_scraping, source_ids)
    return {"message": f"Scraping iniciado para {len(source_ids)} fuente(s).", "source_ids": source_ids}


@router.get("/logs")
def get_scraping_logs(
    limit: int = 50,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    logs = (
        db.query(models.ScrapingLog)
        .order_by(models.ScrapingLog.started_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id"            : l.id,
            "source_id"     : l.source_id,
            "source_name"   : l.source.name if l.source else "—",
            "status"        : l.status,
            "posts_found"   : l.posts_found,
            "comments_found": l.comments_found,
            "message"       : l.message,
            "started_at"    : l.started_at.isoformat(),
            "finished_at"   : l.finished_at.isoformat() if l.finished_at else None,
        }
        for l in logs
    ]


# ------------------------------------------------------------------
# Tarea en background
# ------------------------------------------------------------------

def _run_scraping(source_ids: list):
    db = SessionLocal()
    try:
        # Obtener config de sentimiento
        ai_engine = _get_cfg(db, "ai_engine") or "local"
        ai_key    = _get_cfg(db, "ai_api_key") or ""
        ai_model  = _get_cfg(db, "ai_model")   or ""

        for source_id in source_ids:
            _scrape_source(db, source_id, ai_engine, ai_key, ai_model)
    finally:
        db.close()


def _scrape_source(db: Session, source_id: int, ai_engine: str, ai_key: str, ai_model: str):
    source = db.query(models.InformationSource).filter(
        models.InformationSource.id == source_id
    ).first()
    if not source:
        return

    log = models.ScrapingLog(source_id=source_id, status="running")
    db.add(log)
    db.commit()

    try:
        scraper_cls = {
            "instagram": InstagramScraper,
            "facebook" : FacebookScraper,
            "twitter"  : TwitterScraper,
        }.get(source.social_network)

        if not scraper_cls:
            raise ValueError(f"Red social no soportada: {source.social_network}")

        start_dt = datetime.combine(source.start_date, datetime.min.time())
        scraper  = scraper_cls(source_url=source.url, start_date=start_dt)
        raw_posts = scraper.scrape()

        posts_saved    = 0
        comments_saved = 0

        # Construir mapa topic_name → id
        topics = {t.name: t.id for t in db.query(models.Topic).filter(models.Topic.is_active == True).all()}

        for rp in raw_posts:
            # Detectar tema
            text_for_classification = f"{rp.title} {rp.content}"
            topic_name = classify_topic(text_for_classification)
            topic_id   = topics.get(topic_name) if topic_name else None

            # Sólo guardar posts relacionados con algún eje
            if not topic_id:
                continue

            # Upsert post
            existing = db.query(models.Post).filter(
                models.Post.source_id   == source_id,
                models.Post.external_id == rp.external_id,
            ).first()

            if existing:
                post = existing
            else:
                post = models.Post(
                    source_id   = source_id,
                    topic_id    = topic_id,
                    external_id = rp.external_id,
                    title       = rp.title[:1000] if rp.title else "",
                    content     = rp.content,
                    post_url    = rp.post_url,
                    post_date   = rp.post_date,
                )
                db.add(post)
                db.flush()
                posts_saved += 1

            # Calcular próximo refresh
            _schedule_refresh(post, source)

            # Procesar comentarios
            for rc in rp.comments:
                existing_c = db.query(models.Comment).filter(
                    models.Comment.post_id    == post.id,
                    models.Comment.external_id == rc.external_id,
                ).first()
                if existing_c:
                    continue

                sentiment, score = analyze_sentiment(rc.content, ai_engine, ai_key, ai_model)
                comment = models.Comment(
                    post_id      = post.id,
                    external_id  = rc.external_id,
                    content      = rc.content[:2000],
                    sentiment    = sentiment,
                    sentiment_score = score,
                    author       = rc.author,
                    comment_date = rc.comment_date,
                )
                db.add(comment)
                comments_saved += 1

            # Actualizar contadores del post
            _update_post_counts(db, post)

        db.flush()

        # Actualizar last_scraped_at de la fuente
        source.last_scraped_at = datetime.utcnow()

        total_scraped = len(raw_posts)
        discarded     = total_scraped - posts_saved

        source.last_scraped_at = datetime.utcnow()
        log.status         = "success"
        log.posts_found    = posts_saved
        log.comments_found = comments_saved
        log.message        = (
            f"OK: {posts_saved} posts guardados, {comments_saved} comentarios nuevos. "
            + (f"{discarded} posts descartados (no clasificaron en ningún eje temático). " if discarded else "")
            + (f"0 posts encontrados desde {source.start_date} — verificá la fecha de inicio." if total_scraped == 0 else "")
        )
        log.finished_at    = datetime.utcnow()
        db.commit()
        logger.info("Scraping OK: fuente %d — %d posts, %d comentarios", source_id, posts_saved, comments_saved)

    except Exception as e:
        db.rollback()
        log.status      = "error"
        log.message     = str(e)[:1000]
        log.finished_at = datetime.utcnow()
        db.commit()
        logger.error("Scraping ERROR fuente %d: %s", source_id, e)


def _update_post_counts(db: Session, post: models.Post):
    from sqlalchemy import func
    counts = (
        db.query(models.Comment.sentiment, func.count(models.Comment.id))
        .filter(models.Comment.post_id == post.id)
        .group_by(models.Comment.sentiment)
        .all()
    )
    count_map = {sentiment: cnt for sentiment, cnt in counts}
    post.positive_comments = count_map.get("positive", 0)
    post.negative_comments = count_map.get("negative", 0)
    post.neutral_comments  = count_map.get("neutral",  0)
    post.last_refreshed_at = datetime.utcnow()


REFRESH_MINUTES = {
    "30min": 30,
    "1h"   : 60,
    "4h"   : 240,
    "12h"  : 720,
    "24h"  : 1440,
}
WINDOW_HOURS = {
    "24h"   : 24,
    "48h"   : 48,
    "72h"   : 72,
    "1week" : 168,
}


def _schedule_refresh(post: models.Post, source: models.InformationSource):
    from datetime import timedelta
    now = datetime.utcnow()

    if source.refresh_rate == "never":
        post.next_refresh_at = None
        post.refresh_until   = None
        return

    minutes  = REFRESH_MINUTES.get(source.refresh_rate, 0)
    win_hrs  = WINDOW_HOURS.get(source.refresh_window, 24) if source.refresh_window else 24

    if post.refresh_until is None:
        post.refresh_until = now + timedelta(hours=win_hrs)

    if now < post.refresh_until:
        post.next_refresh_at = now + timedelta(minutes=minutes)
    else:
        post.next_refresh_at = None


def _get_cfg(db: Session, key: str) -> Optional[str]:
    cfg = db.query(models.AppConfig).filter(models.AppConfig.config_key == key).first()
    return cfg.config_value if cfg else None
