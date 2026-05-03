"""
MuniMood — Termómetro Político Municipal
Punto de entrada de la aplicación FastAPI.
"""
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.config import CORS_ORIGINS
from backend.scheduler import start_scheduler, stop_scheduler
from backend.routes import auth, sources, dashboard, topics, posts, config, scraping

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("MuniMood iniciando...")
    start_scheduler()
    yield
    stop_scheduler()
    logger.info("MuniMood detenido.")


app = FastAPI(
    title="MuniMood API",
    description="Termómetro Político Municipal — Backend REST",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# ------------------------------------------------------------------
# CORS
# ------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------
# Rutas API
# ------------------------------------------------------------------
app.include_router(auth.router)
app.include_router(sources.router)
app.include_router(dashboard.router)
app.include_router(topics.router)
app.include_router(posts.router)
app.include_router(config.router)
app.include_router(scraping.router)

# ------------------------------------------------------------------
# Archivos estáticos del frontend
# ------------------------------------------------------------------
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")

if os.path.isdir(FRONTEND_DIR):
    app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

    @app.get("/")
    def root():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

    @app.get("/dashboard")
    def dashboard_page():
        return FileResponse(os.path.join(FRONTEND_DIR, "dashboard.html"))

    @app.get("/sources")
    def sources_page():
        return FileResponse(os.path.join(FRONTEND_DIR, "sources.html"))

    @app.get("/topic-detail")
    def topic_detail_page():
        return FileResponse(os.path.join(FRONTEND_DIR, "topic-detail.html"))

    @app.get("/config")
    def config_page():
        return FileResponse(os.path.join(FRONTEND_DIR, "config.html"))
