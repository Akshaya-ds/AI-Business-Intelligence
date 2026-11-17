
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

from ..core import models
from ..core.db import get_db
from ..core.security import (
    hash_password,
    verify_password,
    create_access_token
)
from ..core.auth import get_required_user

router = APIRouter()


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)


def make_auth_response(user):
    token = create_access_token({"sub": str(user.id)})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email
        }
    }


@router.post("/register")
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    email = data.email.lower()

    existing = db.query(models.User).filter(
        models.User.email == email
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="An account with this email already exists."
        )

    user = models.User(
        name=data.name.strip(),
        email=email,
        hashed_password=hash_password(data.password)
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return make_auth_response(user)


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(
        models.User.email == form_data.username.lower()
    ).first()

    if not user or not verify_password(
        form_data.password,
        user.hashed_password
    ):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password."
        )

    return make_auth_response(user)


@router.get("/me")
def current_user(user=Depends(get_required_user)):
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email
    }
