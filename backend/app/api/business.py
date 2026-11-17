
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core import models, schemas
from ..core.db import get_db
from ..core.auth import get_current_user, get_required_user

router = APIRouter()

@router.get("/")
def get_businesses(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    query = db.query(models.Business).filter(
        models.Business.is_public == True
    )

    if user:
        query = db.query(models.Business).filter(
            (models.Business.is_public == True) |
            (models.Business.owner_id == user.id)
        )

    businesses = query.order_by(models.Business.id).all()

    result = []
    for business in businesses:
        item = schemas.BusinessRead.model_validate(business).model_dump()
        item["is_public"] = business.is_public
        item["is_read_only"] = business.is_public
        result.append(item)

    return result

@router.post("/")
def create_business(
    data: schemas.BusinessCreate,
    db: Session = Depends(get_db),
    user=Depends(get_required_user)
):
    existing = db.query(models.Business).filter(
        models.Business.owner_id == user.id,
        models.Business.name == data.name
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="You already have a business with this name."
        )

    business = models.Business(
        name=data.name,
        type=data.type,
        description=data.description,
        contact_email=data.contact_email,
        owner_id=user.id,
        is_public=False
    )

    db.add(business)
    db.commit()
    db.refresh(business)

    result = schemas.BusinessRead.model_validate(business).model_dump()
    result["is_public"] = False
    result["is_read_only"] = False

    return result

@router.get("/{business_id}")
def get_business(
    business_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    business = db.query(models.Business).filter(
        models.Business.id == business_id
    ).first()

    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    if not business.is_public and (
        not user or business.owner_id != user.id
    ):
        raise HTTPException(status_code=404, detail="Business not found")

    result = schemas.BusinessRead.model_validate(business).model_dump()
    result["is_public"] = business.is_public
    result["is_read_only"] = business.is_public

    return result