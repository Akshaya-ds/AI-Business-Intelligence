
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, JSON, Boolean
)
from sqlalchemy.orm import relationship
from datetime import datetime
from .db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    businesses = relationship("Business", back_populates="owner")


class Business(Base):
    __tablename__ = "businesses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=True)
    description = Column(String, nullable=True)
    contact_email = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Public Demo has owner_id=None and is_public=True.
    # Private businesses belong to one registered user.
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_public = Column(Boolean, default=False, nullable=False)

    owner = relationship("User", back_populates="businesses")

    datasets = relationship(
        "Dataset",
        back_populates="business",
        cascade="all, delete-orphan"
    )
    settings = relationship(
        "BusinessSettings",
        uselist=False,
        back_populates="business",
        cascade="all, delete-orphan"
    )
    models = relationship(
        "MLModel",
        back_populates="business",
        cascade="all, delete-orphan"
    )


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    filename = Column(String, nullable=False)
    filepath = Column(String, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    column_names = Column(JSON, nullable=True)
    column_mapping = Column(JSON, nullable=True)
    row_count = Column(Integer, nullable=True)
    has_date = Column(Integer, default=0)
    has_product_name = Column(Integer, default=0)
    has_category = Column(Integer, default=0)
    has_quantity = Column(Integer, default=0)
    has_price = Column(Integer, default=0)
    has_cost = Column(Integer, default=0)
    has_revenue = Column(Integer, default=0)
    has_stock = Column(Integer, default=0)

    business = relationship("Business", back_populates="datasets")


class MLModel(Base):
    __tablename__ = "ml_models"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    product_name = Column(String, nullable=False)
    model_type = Column(String, nullable=False)
    metrics = Column(JSON, nullable=True)
    file_path = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    business = relationship("Business", back_populates="models")
    dataset = relationship("Dataset")


class BusinessSettings(Base):
    __tablename__ = "business_settings"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(
        Integer,
        ForeignKey("businesses.id"),
        nullable=False,
        unique=True
    )
    active_dataset_id = Column(Integer, nullable=True)
    lead_time_days = Column(Integer, nullable=True)
    safety_stock = Column(Integer, nullable=True)

    business = relationship("Business", back_populates="settings")
