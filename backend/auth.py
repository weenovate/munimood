"""
Utilidades de autenticación: hashing, JWT, verificación de sesión.
"""
import hashlib
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from backend.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from backend.database import get_db
from backend import models

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)


# ------------------------------------------------------------------
# Password helpers
# ------------------------------------------------------------------

def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ------------------------------------------------------------------
# JWT helpers
# ------------------------------------------------------------------

def create_access_token(user_id: int, username: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "username": username, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def store_session(db: Session, user_id: int, token: str):
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    session = models.Session(
        user_id=user_id,
        token_hash=_token_hash(token),
        expires_at=expire,
    )
    db.add(session)
    db.commit()


def revoke_session(db: Session, token: str):
    th = _token_hash(token)
    db.query(models.Session).filter(models.Session.token_hash == th).delete()
    db.commit()


def _is_session_valid(db: Session, token: str) -> bool:
    th = _token_hash(token)
    s = (
        db.query(models.Session)
        .filter(
            models.Session.token_hash == th,
            models.Session.expires_at > datetime.utcnow(),
        )
        .first()
    )
    return s is not None


# ------------------------------------------------------------------
# FastAPI dependency
# ------------------------------------------------------------------

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> models.User:
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Sesión inválida o expirada. Iniciá sesión nuevamente.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not credentials:
        raise exc
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
    except (JWTError, TypeError, ValueError):
        raise exc

    if not _is_session_valid(db, token):
        raise exc

    user = db.query(models.User).filter(
        models.User.id == user_id,
        models.User.is_active == True,
    ).first()
    if not user:
        raise exc
    return user


def require_admin(current_user: models.User = Depends(get_current_user)) -> models.User:
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Se requieren permisos de administrador.")
    return current_user
