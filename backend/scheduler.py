"""
Scheduler de tareas periódicas (APScheduler).
- Refresca posts que están dentro de su ventana de actualización.
- Limpia sesiones y tokens de reset vencidos.
"""
import logging
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import and_

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def start_scheduler():
    global _scheduler
    if _scheduler and _scheduler.running:
        return

    _scheduler = BackgroundScheduler(timezone="America/Argentina/Buenos_Aires")

    # Tarea principal: refrescar posts con next_refresh_at vencido (cada 5 min)
    _scheduler.add_job(_refresh_due_posts,    "interval", minutes=5,  id="refresh_posts")
    # Limpieza de sesiones vencidas (cada hora)
    _scheduler.add_job(_cleanup_expired,      "interval", hours=1,    id="cleanup")

    _scheduler.start()
    logger.info("Scheduler iniciado.")


def stop_scheduler():
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler detenido.")


# ------------------------------------------------------------------
# Tareas
# ------------------------------------------------------------------

def _refresh_due_posts():
    from backend.database import SessionLocal
    from backend import models
    from backend.routes.scraping import _update_post_counts, _schedule_refresh
    from backend.sentiment.analyzer import analyze_sentiment
    from backend.scrapers.instagram_scraper import InstagramScraper
    from backend.scrapers.facebook_scraper   import FacebookScraper
    from backend.scrapers.twitter_scraper    import TwitterScraper

    db = SessionLocal()
    try:
        now = datetime.utcnow()

        # Config de sentimiento
        def _get_cfg(key):
            cfg = db.query(models.AppConfig).filter(models.AppConfig.config_key == key).first()
            return cfg.config_value if cfg else ""

        ai_engine = _get_cfg("ai_engine") or "local"
        ai_key    = _get_cfg("ai_api_key") or ""
        ai_model  = _get_cfg("ai_model")   or ""

        due_posts = (
            db.query(models.Post)
            .filter(
                models.Post.next_refresh_at != None,
                models.Post.next_refresh_at <= now,
                models.Post.refresh_until   >  now,
            )
            .limit(50)
            .all()
        )

        if not due_posts:
            return

        logger.info("Scheduler: %d posts para refrescar", len(due_posts))

        for post in due_posts:
            try:
                source = post.source
                scraper_cls = {
                    "instagram": InstagramScraper,
                    "facebook" : FacebookScraper,
                    "twitter"  : TwitterScraper,
                }.get(source.social_network)

                if not scraper_cls:
                    continue

                from datetime import timedelta
                scraper = scraper_cls(
                    source_url=source.url,
                    start_date=post.post_date or datetime.utcnow() - timedelta(days=1),
                )
                raw_posts = scraper.scrape()

                for rp in raw_posts:
                    if rp.external_id != post.external_id:
                        continue
                    for rc in rp.comments:
                        existing = db.query(models.Comment).filter(
                            models.Comment.post_id     == post.id,
                            models.Comment.external_id == rc.external_id,
                        ).first()
                        if existing:
                            continue
                        sentiment, score = analyze_sentiment(rc.content, ai_engine, ai_key, ai_model)
                        db.add(models.Comment(
                            post_id         = post.id,
                            external_id     = rc.external_id,
                            content         = rc.content[:2000],
                            sentiment       = sentiment,
                            sentiment_score = score,
                            author          = rc.author,
                            comment_date    = rc.comment_date,
                        ))

                _update_post_counts(db, post)
                _schedule_refresh(post, source)

            except Exception as e:
                logger.warning("Scheduler: error refrescando post %d — %s", post.id, e)
                continue

        db.commit()

    except Exception as e:
        db.rollback()
        logger.error("Scheduler _refresh_due_posts error: %s", e)
    finally:
        db.close()


def _cleanup_expired():
    from backend.database import SessionLocal
    from backend import models

    db = SessionLocal()
    try:
        now = datetime.utcnow()
        deleted_sessions = (
            db.query(models.Session)
            .filter(models.Session.expires_at < now)
            .delete()
        )
        deleted_tokens = (
            db.query(models.PasswordResetToken)
            .filter(models.PasswordResetToken.expires_at < now)
            .delete()
        )
        db.commit()
        if deleted_sessions or deleted_tokens:
            logger.info("Cleanup: %d sesiones, %d tokens eliminados", deleted_sessions, deleted_tokens)
    except Exception as e:
        db.rollback()
        logger.error("Scheduler _cleanup_expired error: %s", e)
    finally:
        db.close()
