"""
Scraper de Facebook usando la librería facebook-scraper.
Requiere: pip install facebook-scraper
"""
import logging
from datetime import datetime
from typing import List

from backend.scrapers.base_scraper import BaseScraper, ScrapedPost, ScrapedComment
from backend.config import FACEBOOK_EMAIL, FACEBOOK_PASSWORD

logger = logging.getLogger(__name__)


class FacebookScraper(BaseScraper):

    def scrape(self) -> List[ScrapedPost]:
        try:
            from facebook_scraper import get_posts
        except ImportError:
            logger.error("facebook-scraper no está instalado. Ejecutá: pip install facebook-scraper")
            return []

        handle = self.extract_handle(self.source_url)
        posts: List[ScrapedPost] = []

        credentials = None
        if FACEBOOK_EMAIL and FACEBOOK_PASSWORD:
            credentials = (FACEBOOK_EMAIL, FACEBOOK_PASSWORD)

        try:
            options = {
                "comments": True,
                "reactors": False,
                "progress": False,
            }

            for raw_post in get_posts(
                handle,
                pages=20,
                credentials=credentials,
                options=options,
            ):
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
                    raw_comments = raw_post.get("comments_full") or []
                    for rc in raw_comments:
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
            logger.error("Facebook: error scrapeando '%s' — %s", handle, e)

        logger.info("Facebook @%s: %d posts encontrados desde %s", handle, len(posts), self.start_date.date())
        return posts
