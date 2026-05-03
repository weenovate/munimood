"""
Scraper de Facebook usando la librería facebook-scraper.
Requiere: pip install facebook-scraper lxml_html_clean

Autenticación (en orden de prioridad):
  1. Cookies del navegador (FACEBOOK_COOKIES_FILE en .env) — más confiable desde VPS
  2. Email + contraseña (FACEBOOK_EMAIL / FACEBOOK_PASSWORD en .env)
  3. Anónimo — sólo funciona en páginas completamente públicas
"""
import logging
import os
from datetime import datetime
from typing import List

from backend.scrapers.base_scraper import BaseScraper, ScrapedPost, ScrapedComment
from backend.config import FACEBOOK_EMAIL, FACEBOOK_PASSWORD, FACEBOOK_COOKIES_FILE

logger = logging.getLogger(__name__)


class FacebookScraper(BaseScraper):

    def scrape(self) -> List[ScrapedPost]:
        try:
            from facebook_scraper import get_posts
        except ImportError as _ie:
            raise RuntimeError(
                f"La librería 'facebook-scraper' no se pudo cargar: {_ie}. "
                "Ejecutá: source venv/bin/activate && pip install facebook-scraper lxml_html_clean"
            )

        handle = self.extract_handle(self.source_url)
        posts: List[ScrapedPost] = []

        # -- Determinar método de autenticación --
        cookies_path = FACEBOOK_COOKIES_FILE.strip() if FACEBOOK_COOKIES_FILE else ""
        use_cookies  = bool(cookies_path and os.path.isfile(cookies_path))
        credentials  = None

        if use_cookies:
            logger.info("Facebook: usando cookies del navegador (%s)", cookies_path)
        elif FACEBOOK_EMAIL and FACEBOOK_PASSWORD:
            credentials = (FACEBOOK_EMAIL, FACEBOOK_PASSWORD)
            logger.info("Facebook: usando email/contraseña (puede fallar desde VPS)")
        else:
            logger.warning(
                "Facebook: sin autenticación. "
                "Para páginas que requieren login, exportá las cookies del navegador "
                "y configurá FACEBOOK_COOKIES_FILE en .env"
            )

        try:
            options = {
                "comments": True,
                "reactors": False,
                "progress": False,
            }

            kwargs = dict(pages=20, options=options)
            if use_cookies:
                kwargs["cookies"] = cookies_path
            elif credentials:
                kwargs["credentials"] = credentials

            for raw_post in get_posts(handle, **kwargs):
                try:
                    post_dt = raw_post.get("time")
                    if isinstance(post_dt, datetime):
                        if post_dt < self.start_date:
                            break
                    else:
                        continue

                    text   = raw_post.get("text") or raw_post.get("post_text") or ""
                    title  = text[:120] + ("…" if len(text) > 120 else "")
                    url    = raw_post.get("post_url") or raw_post.get("link") or ""
                    ext_id = raw_post.get("post_id") or url

                    comments: List[ScrapedComment] = []
                    for rc in (raw_post.get("comments_full") or []):
                        try:
                            c_text = rc.get("comment_text") or rc.get("body") or ""
                            if not c_text:
                                continue
                            c_id   = str(rc.get("comment_id") or rc.get("id") or hash(c_text))
                            c_date = rc.get("comment_time") or rc.get("time")
                            c_auth = rc.get("commenter_name") or rc.get("name") or ""
                            comments.append(
                                ScrapedComment(
                                    external_id  = c_id,
                                    content      = c_text,
                                    author       = c_auth,
                                    comment_date = c_date if isinstance(c_date, datetime) else None,
                                )
                            )
                        except Exception:
                            continue

                    posts.append(
                        ScrapedPost(
                            external_id = str(ext_id),
                            title       = title,
                            content     = text,
                            post_url    = url,
                            post_date   = post_dt,
                            comments    = comments,
                        )
                    )
                except Exception as pe:
                    logger.warning("Facebook: error procesando post — %s", pe)
                    continue

        except Exception as e:
            auth_hint = (
                "Exportá las cookies de Facebook desde tu navegador (ver instrucciones abajo) "
                "y configurá FACEBOOK_COOKIES_FILE en .env."
                if not use_cookies else
                f"Las cookies en '{cookies_path}' pueden haber expirado. Volvé a exportarlas."
            )
            raise RuntimeError(
                f"Facebook: error al scrapear '{handle}'. "
                f"Error técnico: {e}. "
                f"{auth_hint}"
            )

        if not posts:
            logger.warning(
                "Facebook '%s': 0 posts desde %s. Verificá la URL y la fecha de inicio.",
                handle, self.start_date.date()
            )
        else:
            logger.info("Facebook '%s': %d posts desde %s", handle, len(posts), self.start_date.date())
        return posts
