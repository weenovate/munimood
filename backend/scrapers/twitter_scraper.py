"""
Scraper de Twitter / X.
Estrategia primaria : API oficial v2 (Bearer Token en .env)
Estrategia fallback : snscrape (sin autenticación, sin garantías)
Requiere: pip install tweepy snscrape
"""
import logging
from datetime import datetime, timezone
from typing import List

from backend.scrapers.base_scraper import BaseScraper, ScrapedPost, ScrapedComment
from backend.config import TWITTER_BEARER

logger = logging.getLogger(__name__)


class TwitterScraper(BaseScraper):

    def scrape(self) -> List[ScrapedPost]:
        if TWITTER_BEARER:
            return self._scrape_v2()
        return self._scrape_snscrape()

    # ------------------------------------------------------------------
    # API oficial v2 con tweepy
    # ------------------------------------------------------------------
    def _scrape_v2(self) -> List[ScrapedPost]:
        try:
            import tweepy
        except ImportError:
            logger.error("tweepy no está instalado. Ejecutá: pip install tweepy")
            return self._scrape_snscrape()

        client = tweepy.Client(bearer_token=TWITTER_BEARER, wait_on_rate_limit=True)
        handle = self.extract_handle(self.source_url)
        posts: List[ScrapedPost] = []

        try:
            user_resp = client.get_user(username=handle, user_fields=["id"])
            if not user_resp.data:
                logger.error("Twitter v2: usuario '%s' no encontrado", handle)
                return []
            user_id = user_resp.data.id

            start_dt = self.start_date
            if start_dt.tzinfo is None:
                start_dt = start_dt.replace(tzinfo=timezone.utc)

            paginator = tweepy.Paginator(
                client.get_users_tweets,
                id=user_id,
                start_time=start_dt,
                tweet_fields=["created_at", "text", "id"],
                max_results=100,
            )

            for tweet in paginator.flatten(limit=500):
                url   = f"https://twitter.com/{handle}/status/{tweet.id}"
                title = tweet.text[:120] + ("…" if len(tweet.text) > 120 else "")
                posts.append(
                    ScrapedPost(
                        external_id = str(tweet.id),
                        title       = title,
                        content     = tweet.text,
                        post_url    = url,
                        post_date   = tweet.created_at.replace(tzinfo=None) if tweet.created_at else None,
                        comments    = [],  # API v2 gratuita no expone respuestas fácilmente
                    )
                )

        except Exception as e:
            logger.error("Twitter v2: error — %s", e)

        logger.info("Twitter @%s (v2): %d tweets", handle, len(posts))
        return posts

    # ------------------------------------------------------------------
    # Fallback: snscrape (sin autenticación)
    # ------------------------------------------------------------------
    def _scrape_snscrape(self) -> List[ScrapedPost]:
        try:
            import snscrape.modules.twitter as sntwitter
        except ImportError:
            logger.error("snscrape no está instalado. Ejecutá: pip install snscrape")
            return []

        handle    = self.extract_handle(self.source_url)
        start_str = self.start_date.strftime("%Y-%m-%d")
        query     = f"from:{handle} since:{start_str}"
        posts: List[ScrapedPost] = []

        try:
            for tweet in sntwitter.TwitterSearchScraper(query).get_items():
                title = tweet.rawContent[:120] + ("…" if len(tweet.rawContent) > 120 else "")
                posts.append(
                    ScrapedPost(
                        external_id = str(tweet.id),
                        title       = title,
                        content     = tweet.rawContent,
                        post_url    = tweet.url,
                        post_date   = tweet.date.replace(tzinfo=None) if tweet.date else None,
                        comments    = [],
                    )
                )
        except Exception as e:
            logger.error("snscrape: error — %s", e)

        logger.info("Twitter @%s (snscrape): %d tweets", handle, len(posts))
        return posts
