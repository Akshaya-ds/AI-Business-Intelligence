
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text

from .core.db import Base, engine, SessionLocal
from .core import models
from .api import (
    business,
    dataset,
    analytics,
    inventory,
    ml,
    forecast,
    assistant,
    auth
)

app = FastAPI(title="AI Business Intelligence Platform")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://ai-business-intelligence-frontend-gnep.onrender.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


def run_database_migration():

    # Create new tables, including users.
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    columns = [
        col["name"]
        for col in inspector.get_columns("businesses")
    ]

    # Add columns to an existing database.
    with engine.begin() as connection:

        if "owner_id" not in columns:
            connection.execute(text(
                "ALTER TABLE businesses ADD COLUMN owner_id INTEGER"
            ))

        if "is_public" not in columns:
            connection.execute(text(
                "ALTER TABLE businesses "
                "ADD COLUMN is_public BOOLEAN NOT NULL DEFAULT 0"
            ))

    # Preserve Demo and remove the old Clothing business.
    db = SessionLocal()

    try:
        demo = db.query(models.Business).filter(
            models.Business.name.ilike("demo")
        ).first()

        if demo:
            demo.owner_id = None
            demo.is_public = True

        clothing_businesses = db.query(models.Business).filter(
            models.Business.name.ilike("clothing")
        ).all()

        for clothing in clothing_businesses:

            # Remove associated model files and records.
            old_models = db.query(models.MLModel).filter(
                models.MLModel.business_id == clothing.id
            ).all()

            for model in old_models:
                if model.file_path and os.path.isfile(model.file_path):
                    try:
                        os.remove(model.file_path)
                    except OSError:
                        pass

                db.delete(model)

            # Remove dataset files and records.
            old_datasets = db.query(models.Dataset).filter(
                models.Dataset.business_id == clothing.id
            ).all()

            for dataset in old_datasets:
                if dataset.filepath and os.path.isfile(dataset.filepath):
                    try:
                        os.remove(dataset.filepath)
                    except OSError:
                        pass

                db.delete(dataset)

            settings = db.query(models.BusinessSettings).filter(
                models.BusinessSettings.business_id == clothing.id
            ).first()

            if settings:
                db.delete(settings)

            db.delete(clothing)

        db.commit()

        print("Database migration completed.")
        print("Demo business is public.")
        print("Old Clothing business data removed.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


run_database_migration()


# API Routes
app.include_router(
    auth.router,
    prefix="/api/auth",
    tags=["Authentication"]
)

app.include_router(
    business.router,
    prefix="/api/businesses",
    tags=["Businesses"]
)

app.include_router(
    dataset.router,
    prefix="/api/datasets",
    tags=["Datasets"]
)

app.include_router(
    analytics.router,
    prefix="/api/analytics",
    tags=["Analytics"]
)

app.include_router(
    inventory.router,
    prefix="/api/inventory",
    tags=["Inventory"]
)

app.include_router(
    ml.router,
    prefix="/api/ml",
    tags=["Machine Learning"]
)

app.include_router(
    forecast.router,
    prefix="/api/forecast",
    tags=["Forecasting"]
)

app.include_router(
    assistant.router,
    prefix="/api/assistant",
    tags=["AI Assistant"]
)


@app.get("/")
def root():
    return {
        "message": "AI Business Intelligence API is running"
    }
