import datetime
from typing import Optional, Any, Union
import bcrypt
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from backend.app.config import settings
from backend.app.models.user import User


def get_password_hash(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a hashed bcrypt password."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False


def create_access_token(
    subject: Union[str, Any],
    role: str,
    expires_delta: Optional[datetime.timedelta] = None,
) -> str:
    """Create a signed JWT access token containing subject (username) and role."""
    if expires_delta:
        expire = datetime.datetime.now(datetime.timezone.utc) + expires_delta
    else:
        expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "role": role,
    }
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return encoded_jwt


def authenticate_user(
    db: Session,
    username_or_email: str,
    password: str,
) -> Optional[User]:
    """Authenticate a user by username or email and verify password."""
    user = (
        db.query(User)
        .filter(
            (User.username == username_or_email) | (User.email == username_or_email)
        )
        .first()
    )
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
