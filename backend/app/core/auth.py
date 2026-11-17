
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from . import models
from .db import get_db
from .security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login",
    auto_error=False
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    if not token:
        return None

    payload = decode_access_token(token)

    if not payload or not payload.get("sub"):
        return None

    try:
        user_id = int(payload["sub"])
    except (ValueError, TypeError):
        return None

    return db.query(models.User).filter(
        models.User.id == user_id
    ).first()


def get_required_user(
    current_user=Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please login to access this feature."
        )
    return current_user


def get_accessible_business(
    business_id: int,
    db: Session,
    current_user=None
):
    business = db.query(models.Business).filter(
        models.Business.id == business_id
    ).first()

    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    if business.is_public:
        return business

    if not current_user or business.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Business not found")

    return business
