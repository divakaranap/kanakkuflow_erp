from typing import List
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.database import get_db
from backend.app.models.user import User, UserRole
from backend.app.schemas.auth import TokenPayload

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenPayload(sub=username, role=payload.get("role"))
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.username == token_data.sub).first()
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account",
        )
    return user


def require_roles(allowed_roles: List[UserRole]):
    """Enforce role-based access control for endpoints."""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted for role '{current_user.role.value}'. Requires one of: {[r.value for r in allowed_roles]}",
            )
        return current_user
    return role_checker


# Convenient role dependencies
require_admin_or_owner = require_roles([UserRole.ADMIN, UserRole.OWNER])
require_owner = require_roles([UserRole.OWNER])
require_salesman = require_roles([UserRole.SALESMAN, UserRole.ADMIN, UserRole.OWNER])
require_production = require_roles([UserRole.PRODUCTION, UserRole.ADMIN, UserRole.OWNER])
require_auditor = require_roles([UserRole.AUDITOR, UserRole.OWNER, UserRole.ADMIN])
