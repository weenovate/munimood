"""
Script de inicialización de la base de datos.
Crea las tablas y el usuario administrador inicial.
Uso: python -m backend.init_db
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import engine, SessionLocal
from backend import models
from backend.auth import hash_password
from datetime import datetime


def init():
    print("Creando tablas...")
    models.Base.metadata.create_all(bind=engine)
    print("Tablas creadas.")

    db = SessionLocal()
    try:
        # Usuario inicial
        existing = db.query(models.User).filter(models.User.username == "muniadmin").first()
        if not existing:
            admin = models.User(
                username     = "muniadmin",
                email        = "admin@municipio.gob.ar",
                password_hash= hash_password("Ramallo2026"),
                full_name    = "Administrador Municipal",
                is_active    = True,
                is_admin     = True,
            )
            db.add(admin)
            print("Usuario 'muniadmin' creado.")

        # Ejes temáticos
        default_topics = [
            ("Economía",       "bi-graph-up-arrow",    1),
            ("Desarrollo",     "bi-buildings",         2),
            ("Seguridad",      "bi-shield-check",      3),
            ("Obras Públicas", "bi-cone-striped",      4),
            ("Educación",      "bi-mortarboard",       5),
            ("Salud",          "bi-heart-pulse",       6),
            ("Turismo",        "bi-map",               7),
            ("Medio Ambiente", "bi-tree",              8),
            ("Entretenimiento","bi-music-note-beamed", 9),
        ]
        for name, icon, order in default_topics:
            if not db.query(models.Topic).filter(models.Topic.name == name).first():
                db.add(models.Topic(name=name, icon=icon, display_order=order, is_active=True))

        # Config semáforo por defecto
        if not db.query(models.TrafficLightConfig).first():
            db.add(models.TrafficLightConfig(
                green_min_pct=61.0, yellow_min_pct=31.0,
                yellow_max_pct=60.0, red_max_pct=30.0,
            ))

        # Config AI por defecto
        defaults = {
            "ai_engine" : "local",
            "ai_api_key": "",
            "ai_model"  : "",
        }
        for key, val in defaults.items():
            if not db.query(models.AppConfig).filter(models.AppConfig.config_key == key).first():
                db.add(models.AppConfig(config_key=key, config_value=val))

        db.commit()
        print("Base de datos inicializada correctamente.")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init()
