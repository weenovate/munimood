from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend import models
from backend.auth import get_current_user, require_admin, hash_password, verify_password
from backend.database import get_db

router = APIRouter(prefix="/api/config", tags=["config"])


# ------------------------------------------------------------------
# Schemas
# ------------------------------------------------------------------

class TrafficLightUpdate(BaseModel):
    green_min_pct : float
    yellow_min_pct: float
    yellow_max_pct: float
    red_max_pct   : float


class AIEngineUpdate(BaseModel):
    engine : str  # local | pysentimiento | openai | claude | gemini
    api_key: str = ""
    model  : str = ""


class UserCreate(BaseModel):
    username  : str
    email     : str
    full_name : str = ""
    password  : str
    is_admin  : bool = False


class UserUpdate(BaseModel):
    email    : str
    full_name: str = ""
    is_active: bool = True
    is_admin : bool = False


class PasswordChange(BaseModel):
    current_password: str
    new_password    : str


# ------------------------------------------------------------------
# Semáforo
# ------------------------------------------------------------------

@router.get("/traffic-light")
def get_traffic_light(
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    tl = db.query(models.TrafficLightConfig).first()
    if not tl:
        tl = models.TrafficLightConfig()
        db.add(tl)
        db.commit()
        db.refresh(tl)
    return {
        "green_min_pct" : tl.green_min_pct,
        "yellow_min_pct": tl.yellow_min_pct,
        "yellow_max_pct": tl.yellow_max_pct,
        "red_max_pct"   : tl.red_max_pct,
    }


@router.put("/traffic-light")
def update_traffic_light(
    body: TrafficLightUpdate,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin),
):
    if not (0 <= body.red_max_pct < body.yellow_min_pct <= body.yellow_max_pct < body.green_min_pct <= 100):
        raise HTTPException(400, "Los rangos del semáforo no son válidos. Verificá que rojo < amarillo < verde.")

    tl = db.query(models.TrafficLightConfig).first()
    if not tl:
        tl = models.TrafficLightConfig()
        db.add(tl)

    tl.green_min_pct  = body.green_min_pct
    tl.yellow_min_pct = body.yellow_min_pct
    tl.yellow_max_pct = body.yellow_max_pct
    tl.red_max_pct    = body.red_max_pct
    db.commit()
    return {"message": "Configuración del semáforo actualizada."}


# ------------------------------------------------------------------
# Motor de IA
# ------------------------------------------------------------------

VALID_ENGINES = {"local", "pysentimiento", "openai", "claude", "gemini"}


@router.get("/ai-engine")
def get_ai_engine(
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    engine  = _get_config(db, "ai_engine")  or "local"
    model   = _get_config(db, "ai_model")   or ""
    has_key = bool(_get_config(db, "ai_api_key"))
    return {"engine": engine, "model": model, "has_api_key": has_key}


@router.put("/ai-engine")
def update_ai_engine(
    body: AIEngineUpdate,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin),
):
    if body.engine not in VALID_ENGINES:
        raise HTTPException(400, f"Motor inválido. Opciones: {VALID_ENGINES}")
    _set_config(db, "ai_engine", body.engine)
    if body.api_key:
        _set_config(db, "ai_api_key", body.api_key)
    _set_config(db, "ai_model", body.model)
    db.commit()
    return {"message": "Motor de IA actualizado."}


# ------------------------------------------------------------------
# Usuarios (CRUD)
# ------------------------------------------------------------------

@router.get("/users")
def list_users(
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin),
):
    users = db.query(models.User).order_by(models.User.username).all()
    return [_serialize_user(u) for u in users]


@router.post("/users", status_code=201)
def create_user(
    body: UserCreate,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin),
):
    if db.query(models.User).filter(models.User.username == body.username).first():
        raise HTTPException(400, "El nombre de usuario ya existe.")
    if db.query(models.User).filter(models.User.email == body.email).first():
        raise HTTPException(400, "El email ya está registrado.")
    if len(body.password) < 6:
        raise HTTPException(400, "La contraseña debe tener al menos 6 caracteres.")

    user = models.User(
        username     = body.username,
        email        = body.email,
        full_name    = body.full_name,
        password_hash= hash_password(body.password),
        is_admin     = body.is_admin,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _serialize_user(user)


@router.put("/users/{user_id}")
def update_user(
    user_id: int,
    body: UserUpdate,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin),
):
    user = _get_user_or_404(db, user_id)
    user.email     = body.email
    user.full_name = body.full_name
    user.is_active = body.is_active
    user.is_admin  = body.is_admin
    db.commit()
    return _serialize_user(user)


@router.put("/users/{user_id}/password")
def change_user_password(
    user_id: int,
    body: PasswordChange,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # Solo el propio usuario o un admin puede cambiar la contraseña
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(403, "No tenés permiso para cambiar esta contraseña.")

    user = _get_user_or_404(db, user_id)
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(400, "La contraseña actual es incorrecta.")
    if len(body.new_password) < 6:
        raise HTTPException(400, "La nueva contraseña debe tener al menos 6 caracteres.")

    user.password_hash = hash_password(body.new_password)
    db.commit()
    return {"message": "Contraseña actualizada."}


@router.delete("/users/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin),
):
    if current_user.id == user_id:
        raise HTTPException(400, "No podés eliminar tu propio usuario.")
    user = _get_user_or_404(db, user_id)
    db.delete(user)
    db.commit()


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _get_config(db: Session, key: str) -> Optional[str]:
    cfg = db.query(models.AppConfig).filter(models.AppConfig.config_key == key).first()
    return cfg.config_value if cfg else None


def _set_config(db: Session, key: str, value: str):
    cfg = db.query(models.AppConfig).filter(models.AppConfig.config_key == key).first()
    if cfg:
        cfg.config_value = value
    else:
        db.add(models.AppConfig(config_key=key, config_value=value))


def _get_user_or_404(db: Session, user_id: int) -> models.User:
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(404, "Usuario no encontrado.")
    return user


def _serialize_user(u: models.User) -> dict:
    return {
        "id"        : u.id,
        "username"  : u.username,
        "email"     : u.email,
        "full_name" : u.full_name,
        "is_active" : u.is_active,
        "is_admin"  : u.is_admin,
        "created_at": u.created_at.isoformat(),
    }
