from datetime import datetime, timedelta, timezone
import hashlib

from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
settings = get_settings()


def hash_password(password: str) -> str:
    try:
        return pwd_context.hash(password)
    except Exception:
        digest = hashlib.sha256(password.encode("utf-8")).hexdigest()
        return f"sha256${digest}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if hashed_password.startswith("sha256$"):
        digest = hashlib.sha256(plain_password.encode("utf-8")).hexdigest()
        return hashed_password == f"sha256${digest}"
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        digest = hashlib.sha256(plain_password.encode("utf-8")).hexdigest()
        return hashed_password == f"sha256${digest}"


def create_access_token(*, subject: str, is_admin: bool, expires_delta: timedelta | None = None) -> str:
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    to_encode = {"sub": subject, "is_admin": is_admin, "exp": expire}
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise credentials_exception from exc

    user_id = payload.get("sub")
    if not user_id:
        raise credentials_exception

    return payload
