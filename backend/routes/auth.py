import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from backend import models
from backend.auth import (
    hash_password, verify_password, create_access_token,
    store_session, revoke_session, get_current_user,
)
from backend.database import get_db
from backend.email_service import send_password_reset

router = APIRouter(prefix="/api/auth", tags=["auth"])


# ------------------------------------------------------------------
# Schemas
# ------------------------------------------------------------------

class LoginRequest(BaseModel):
    username: str
    password: str


class ResetRequestBody(BaseModel):
    email: str


class ResetPasswordBody(BaseModel):
    token: str
    new_password: str


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------

@router.post("/login")
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = (
        db.query(models.User)
        .filter(
            (models.User.username == body.username) | (models.User.email == body.username),
            models.User.is_active == True,
        )
        .first()
    )
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos.",
        )
    token = create_access_token(user.id, user.username)
    store_session(db, user.id, token)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "is_admin": user.is_admin,
        },
    }


@router.post("/logout")
def logout(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Token extraído desde el header — lo revocamos
    # La dependencia ya lo validó; aquí simplemente lo eliminamos
    return {"message": "Sesión cerrada correctamente."}


@router.post("/reset-password-request")
def reset_password_request(body: ResetRequestBody, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == body.email).first()
    # Siempre respondemos OK para no revelar si el email existe
    if user:
        token = secrets.token_urlsafe(32)
        expires = datetime.utcnow() + timedelta(hours=1)
        prt = models.PasswordResetToken(
            user_id=user.id, token=token, expires_at=expires
        )
        db.add(prt)
        db.commit()
        try:
            send_password_reset(user.email, user.username, token)
        except Exception:
            pass  # No revelar error de SMTP al cliente
    return {"message": "Si el email existe, recibirás un enlace para restablecer tu contraseña."}


@router.post("/reset-password")
def reset_password(body: ResetPasswordBody, db: Session = Depends(get_db)):
    prt = (
        db.query(models.PasswordResetToken)
        .filter(
            models.PasswordResetToken.token == body.token,
            models.PasswordResetToken.used == False,
            models.PasswordResetToken.expires_at > datetime.utcnow(),
        )
        .first()
    )
    if not prt:
        raise HTTPException(status_code=400, detail="Token inválido o expirado.")
    if len(body.new_password) < 6:
        raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 6 caracteres.")

    user = db.query(models.User).filter(models.User.id == prt.user_id).first()
    user.password_hash = hash_password(body.new_password)
    prt.used = True
    db.commit()
    return {"message": "Contraseña actualizada correctamente."}


@router.get("/me")
def me(current_user: models.User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "is_admin": current_user.is_admin,
    }
