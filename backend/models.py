from datetime import datetime
from sqlalchemy import (
    Column, Integer, Float, String, Text, Boolean,
    DateTime, Date, Enum, ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from backend.database import Base


class User(Base):
    __tablename__ = "users"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    username     = Column(String(80), nullable=False, unique=True)
    email        = Column(String(255), nullable=False, unique=True)
    password_hash= Column(String(255), nullable=False)
    full_name    = Column(String(255))
    is_active    = Column(Boolean, nullable=False, default=True)
    is_admin     = Column(Boolean, nullable=False, default=False)
    created_at   = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at   = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class Session(Base):
    __tablename__ = "sessions"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    user_id    = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String(255), nullable=False, unique=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    user = relationship("User")


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    user_id    = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token      = Column(String(255), nullable=False, unique=True)
    expires_at = Column(DateTime, nullable=False)
    used       = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    user = relationship("User")


class Topic(Base):
    __tablename__ = "topics"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    name          = Column(String(120), nullable=False, unique=True)
    icon          = Column(String(60), default="bi-circle")
    display_order = Column(Integer, nullable=False, default=0)
    is_active     = Column(Boolean, nullable=False, default=True)
    created_at    = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at    = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    posts = relationship("Post", back_populates="topic")


class InformationSource(Base):
    __tablename__ = "information_sources"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    name           = Column(String(255), nullable=False)
    url            = Column(String(1024), nullable=False)
    social_network = Column(Enum("facebook", "instagram", "twitter"), nullable=False)
    profile_handle = Column(String(255))
    start_date     = Column(Date, nullable=False)
    refresh_rate   = Column(
        Enum("30min", "1h", "4h", "12h", "24h", "never"),
        nullable=False, default="never"
    )
    refresh_window = Column(Enum("24h", "48h", "72h", "1week"), nullable=True)
    is_active      = Column(Boolean, nullable=False, default=True)
    last_scraped_at= Column(DateTime, nullable=True)
    created_at     = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at     = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    posts = relationship("Post", back_populates="source")


class Post(Base):
    __tablename__ = "posts"

    id                = Column(Integer, primary_key=True, autoincrement=True)
    source_id         = Column(Integer, ForeignKey("information_sources.id", ondelete="CASCADE"), nullable=False)
    topic_id          = Column(Integer, ForeignKey("topics.id", ondelete="SET NULL"), nullable=True)
    external_id       = Column(String(255))
    title             = Column(String(1024))
    content           = Column(Text)
    post_url          = Column(String(2048))
    post_date         = Column(DateTime)
    positive_comments = Column(Integer, nullable=False, default=0)
    negative_comments = Column(Integer, nullable=False, default=0)
    neutral_comments  = Column(Integer, nullable=False, default=0)
    last_refreshed_at = Column(DateTime, nullable=True)
    next_refresh_at   = Column(DateTime, nullable=True)
    refresh_until     = Column(DateTime, nullable=True)
    created_at        = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at        = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    source   = relationship("InformationSource", back_populates="posts")
    topic    = relationship("Topic", back_populates="posts")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("source_id", "external_id", name="uq_source_external"),
    )


class Comment(Base):
    __tablename__ = "comments"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    post_id         = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    external_id     = Column(String(255))
    content         = Column(Text, nullable=False)
    sentiment       = Column(Enum("positive", "negative", "neutral"), nullable=False, default="neutral")
    sentiment_score = Column(Float, default=0.0)
    author          = Column(String(255))
    comment_date    = Column(DateTime)
    created_at      = Column(DateTime, nullable=False, default=datetime.utcnow)

    post = relationship("Post", back_populates="comments")

    __table_args__ = (
        UniqueConstraint("post_id", "external_id", name="uq_post_external"),
    )


class TrafficLightConfig(Base):
    __tablename__ = "traffic_light_config"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    green_min_pct  = Column(Float, nullable=False, default=61.0)
    yellow_min_pct = Column(Float, nullable=False, default=31.0)
    yellow_max_pct = Column(Float, nullable=False, default=60.0)
    red_max_pct    = Column(Float, nullable=False, default=30.0)
    updated_at     = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class AppConfig(Base):
    __tablename__ = "app_config"

    config_key   = Column(String(100), primary_key=True)
    config_value = Column(Text)
    updated_at   = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class ScrapingLog(Base):
    __tablename__ = "scraping_logs"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    source_id      = Column(Integer, ForeignKey("information_sources.id", ondelete="SET NULL"), nullable=True)
    status         = Column(Enum("running", "success", "error", "partial"), nullable=False, default="running")
    posts_found    = Column(Integer, default=0)
    comments_found = Column(Integer, default=0)
    message        = Column(Text)
    started_at     = Column(DateTime, nullable=False, default=datetime.utcnow)
    finished_at    = Column(DateTime, nullable=True)

    source = relationship("InformationSource")
