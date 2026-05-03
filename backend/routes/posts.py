import re
from collections import Counter
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from backend import models
from backend.auth import get_current_user
from backend.database import get_db

router = APIRouter(prefix="/api", tags=["posts"])


@router.get("/topics/{topic_id}/posts")
def list_posts_by_topic(
    topic_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    topic = db.query(models.Topic).filter(models.Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(404, "Eje no encontrado.")

    q = (
        db.query(models.Post)
        .filter(models.Post.topic_id == topic_id)
        .order_by(desc(models.Post.post_date))
    )
    total = q.count()
    posts = q.offset((page - 1) * per_page).limit(per_page).all()

    return {
        "topic"   : {"id": topic.id, "name": topic.name, "icon": topic.icon},
        "total"   : total,
        "page"    : page,
        "per_page": per_page,
        "posts"   : [_serialize_post(p) for p in posts],
    }


@router.get("/posts/{post_id}")
def get_post_detail(
    post_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(404, "Posteo no encontrado.")

    total = post.positive_comments + post.negative_comments + post.neutral_comments
    pos_pct = round(post.positive_comments / total * 100, 1) if total else 0
    neg_pct = round(post.negative_comments / total * 100, 1) if total else 0

    # Extraer frases negativas relevantes
    neg_phrases = _extract_negative_phrases(db, post_id)

    return {
        "id"              : post.id,
        "title"           : post.title,
        "content"         : post.content,
        "post_url"        : post.post_url,
        "post_date"       : post.post_date.isoformat() if post.post_date else None,
        "source"          : {
            "id"            : post.source.id,
            "name"          : post.source.name,
            "social_network": post.source.social_network,
        },
        "topic"           : {
            "id"  : post.topic.id,
            "name": post.topic.name,
        } if post.topic else None,
        "positive_comments": post.positive_comments,
        "negative_comments": post.negative_comments,
        "neutral_comments" : post.neutral_comments,
        "total_comments"   : total,
        "pos_pct"          : pos_pct,
        "neg_pct"          : neg_pct,
        "negative_phrases" : neg_phrases,
    }


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

STOPWORDS_ES = {
    "de","la","el","en","y","a","que","los","las","un","una","por","con","no","se","su",
    "es","al","del","lo","le","más","pero","este","esta","muy","como","ya","sus","todo",
    "cuando","hay","tiene","para","fue","son","yo","me","mi","si","te","tu","nos","les",
    "también","porque","puede","han","ha","ser","era","así","donde","sobre","entre",
    "esto","eso","otro","otra","todos","todas","bien","aquí","allí","qué","cómo","quién",
}


def _extract_negative_phrases(db: Session, post_id: int, top_n: int = 10) -> list:
    neg_comments = (
        db.query(models.Comment.content)
        .filter(
            models.Comment.post_id == post_id,
            models.Comment.sentiment == "negative",
        )
        .limit(200)
        .all()
    )

    word_counter: Counter = Counter()
    bigram_counter: Counter = Counter()

    for (text,) in neg_comments:
        # Normalizar
        text_n = text.lower()
        text_n = re.sub(r"[^\w\s]", " ", text_n)
        words = [w for w in text_n.split() if len(w) > 3 and w not in STOPWORDS_ES]

        word_counter.update(words)
        bigrams = [f"{words[i]} {words[i+1]}" for i in range(len(words) - 1)]
        bigram_counter.update(bigrams)

    phrases = []
    for phrase, count in bigram_counter.most_common(top_n):
        if count >= 2:
            phrases.append({"phrase": phrase, "count": count})

    if len(phrases) < top_n:
        for word, count in word_counter.most_common(top_n - len(phrases)):
            if count >= 2 and word not in {p["phrase"] for p in phrases}:
                phrases.append({"phrase": word, "count": count})

    return sorted(phrases, key=lambda x: x["count"], reverse=True)[:top_n]


def _serialize_post(p: models.Post) -> dict:
    total = p.positive_comments + p.negative_comments + p.neutral_comments
    return {
        "id"              : p.id,
        "title"           : p.title,
        "post_date"       : p.post_date.isoformat() if p.post_date else None,
        "post_url"        : p.post_url,
        "source_name"     : p.source.name if p.source else "",
        "social_network"  : p.source.social_network if p.source else "",
        "positive_comments": p.positive_comments,
        "negative_comments": p.negative_comments,
        "total_comments"  : total,
    }
