"""
Scraper de Instagram usando la librería instaloader.
Requiere: pip install instaloader
"""
import logging
from datetime import datetime, timezone
from typing import List

from backend.scrapers.base_scraper import BaseScraper, ScrapedPost, ScrapedComment
from backend.config import INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD

logger = logging.getLogger(__name__)


class InstagramScraper(BaseScraper):

    def scrape(self) -> List[ScrapedPost]:
        try:
            import instaloader
        except ImportError:
            logger.error("instaloader no está instalado. Ejecutá: pip install instaloader")
            return []

        L = instaloader.Instaloader(
            download_pictures=False,
            download_videos=False,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=True,
            save_metadata=False,
            compress_json=False,
            quiet=True,
        )

        # Login opcional pero recomendado para obtener más datos
        if INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD:
            try:
                L.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
                logger.info("Instagram: sesión iniciada como %s", INSTAGRAM_USERNAME)
            except Exception as e:
                logger.warning("Instagram: no se pudo iniciar sesión — %s", e)

        handle = self.extract_handle(self.source_url)
        posts: List[ScrapedPost] = []

        try:
            profile = instaloader.Profile.from_username(L.context, handle)
        except Exception as e:
            logger.error("Instagram: no se pudo cargar el perfil '%s' — %s", handle, e)
            return []

        start_ts = self.start_date.replace(tzinfo=timezone.utc) if self.start_date.tzinfo is None else self.start_date

        for post in profile.get_posts():
            try:
                post_dt = post.date_utc
                if post_dt.tzinfo is None:
                    post_dt = post_dt.replace(tzinfo=timezone.utc)

                if post_dt < start_ts:
                    break  # Los posts están en orden cronológico inverso

                caption = post.caption or ""
                title   = caption[:120] + ("…" if len(caption) > 120 else "")
                url     = f"https://www.instagram.com/p/{post.shortcode}/"

                comments: List[ScrapedComment] = []
                try:
                    for comment in post.get_comments():
                        comments.append(
                            ScrapedComment(
                                external_id  = str(comment.id),
                                content      = comment.text,
                                author       = comment.owner.username,
                                comment_date = comment.created_at_utc,
                            )
                        )
                except Exception as ce:
                    logger.warning("Instagram: error al obtener comentarios de %s — %s", url, ce)

                posts.append(
                    ScrapedPost(
                        external_id = post.shortcode,
                        title       = title,
                        content     = caption,
                        post_url    = url,
                        post_date   = post_dt.replace(tzinfo=None),
                        comments    = comments,
                    )
                )
            except Exception as pe:
                logger.warning("Instagram: error procesando post — %s", pe)
                continue

        logger.info("Instagram @%s: %d posts encontrados desde %s", handle, len(posts), self.start_date.date())
        return posts
