"""
Configuración central de la aplicación MuniMood.
Las credenciales sensibles se leen desde el archivo .env
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ------------------------------------------------------------------
# Base de datos MySQL
# ------------------------------------------------------------------
DB_HOST     = os.getenv("DB_HOST", "localhost")
DB_PORT     = int(os.getenv("DB_PORT", "3306"))
DB_NAME     = os.getenv("DB_NAME", "munimood")
DB_USER     = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

DATABASE_URL = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    "?charset=utf8mb4"
)

# ------------------------------------------------------------------
# JWT / Sesiones
# ------------------------------------------------------------------
SECRET_KEY                  = os.getenv("SECRET_KEY", "cambia-esta-clave-secreta-en-produccion")
ALGORITHM                   = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("SESSION_EXPIRE_MINUTES", "480"))  # 8 horas

# ------------------------------------------------------------------
# Correo SMTP  ← MODIFICAR ESTAS CREDENCIALES EN EL ARCHIVO .env
# ------------------------------------------------------------------
SMTP_HOST     = os.getenv("SMTP_HOST", "smtp.example.com")
SMTP_PORT     = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER     = os.getenv("SMTP_USER", "usuario@example.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM     = os.getenv("SMTP_FROM", "noreply@municipio.gob.ar")
SMTP_USE_TLS  = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

# ------------------------------------------------------------------
# URL pública de la aplicación (para links en mails)
# ------------------------------------------------------------------
APP_URL = os.getenv("APP_URL", "http://localhost:8000")

# ------------------------------------------------------------------
# Scraping / credenciales de redes sociales (opcionales)
# ------------------------------------------------------------------
INSTAGRAM_USERNAME = os.getenv("INSTAGRAM_USERNAME", "")
INSTAGRAM_PASSWORD = os.getenv("INSTAGRAM_PASSWORD", "")
FACEBOOK_EMAIL     = os.getenv("FACEBOOK_EMAIL", "")
FACEBOOK_PASSWORD  = os.getenv("FACEBOOK_PASSWORD", "")
TWITTER_BEARER     = os.getenv("TWITTER_BEARER_TOKEN", "")

# ------------------------------------------------------------------
# Miscelánea
# ------------------------------------------------------------------
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000").split(",")
