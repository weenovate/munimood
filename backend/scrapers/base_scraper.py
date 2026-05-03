"""
Clase base para todos los scrapers de redes sociales.
"""
import logging
import re
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class ScrapedPost:
    def __init__(
        self,
        external_id: str,
        title: str,
        content: str,
        post_url: str,
        post_date: Optional[datetime],
        comments: List["ScrapedComment"],
    ):
        self.external_id = external_id
        self.title       = title
        self.content     = content
        self.post_url    = post_url
        self.post_date   = post_date
        self.comments    = comments


class ScrapedComment:
    def __init__(
        self,
        external_id: str,
        content: str,
        author: str,
        comment_date: Optional[datetime],
    ):
        self.external_id  = external_id
        self.content      = content
        self.author       = author
        self.comment_date = comment_date


class BaseScraper(ABC):
    """Interfaz común para scrapers. Cada red implementa `scrape()`."""

    def __init__(self, source_url: str, start_date: datetime, **kwargs):
        self.source_url = source_url
        self.start_date = start_date
        self.kwargs     = kwargs
        self.logger     = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def scrape(self) -> List[ScrapedPost]:
        """Devuelve lista de posteos con sus comentarios."""
        ...

    @staticmethod
    def extract_handle(url: str) -> str:
        """Extrae el handle/usuario de una URL de red social."""
        url = url.rstrip("/")
        parts = url.split("/")
        for part in reversed(parts):
            if part and not part.startswith("http") and "." not in part:
                return part.lstrip("@")
        return url
