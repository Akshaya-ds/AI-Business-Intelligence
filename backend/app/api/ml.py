
import os

from fastapi import (
    APIRouter, Depends, BackgroundTasks, HTTPException
)
from sqlalchemy.orm import Session

from ..core import db, models, schemas
from ..core.auth import get_current_user, get_accessible_business
from ..core.preprocess import preprocess_file
from ..core.ml_training import train_all_products

from typing import Dict, List

router = APIRouter()

# Directory where trained model files are stored.
MODEL_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../models")
)


def _get_latest_dataset(
    business_id: int,
    database: Session
) -> models.Dataset:

    ds = (
        database.query(models.Dataset)
        .filter(models.Dataset.business_id == business_id)
        .order_by(models.Dataset.uploaded_at.desc())
        .first()
    )

    if not ds:
        raise HTTPException(
            status_code=404,
            detail="No dataset for this business"
        )

    return ds


@router.post(
    "/train/{business_id}",
    response_model=Dict[str, str]
)
def start_training(
    business_id: int,
    background_tasks: BackgroundTasks,
    database: Session = Depends(db.get_db),
    user=Depends(get_current_user),
):
    # Verify ownership before accessing the dataset.
    business = get_accessible_business(
        business_id, database, user
    )

    # Public Demo is read-only.
    if business.is_public:
        raise HTTPException(
            status_code=403,
            detail="ML training is disabled for the public Demo business."
        )

    ds = _get_latest_dataset(
        business_id, database
    )

    # Schedule background training task.
    background_tasks.add_task(
        _train_and_store,
        ds.filepath,
        business_id,
        ds.id
    )

    return {"status": "training started"}


def _train_and_store(
    filepath: str,
    business_id: int,
    dataset_id: int
):
    try:
        # Preprocess the selected dataset.
        agg_df, mapping = preprocess_file(filepath)

        # Store models separately for each business and dataset.
        dataset_model_dir = os.path.join(
            MODEL_ROOT,
            f"business_{business_id}",
            f"dataset_{dataset_id}"
        )

        # Train one model for each product.
        results = train_all_products(
            agg_df,
            dataset_model_dir
        )

        # Create a new database session for background training.
        session = db.SessionLocal()

        try:
            for product, info in results.items():

                if "model_path" in info:
                    model_rec = models.MLModel(
                        business_id=business_id,
                        dataset_id=dataset_id,
                        product_name=product,
                        model_type=(
                            "XGBoost"
                            if "xgboost" in info["model_path"].lower()
                            else "RandomForest"
                        ),
                        metrics=info.get("metrics"),
                        file_path=info["model_path"],
                    )

                    session.add(model_rec)

            session.commit()

        finally:
            session.close()

    except Exception as e:
        print(f"Training error: {e}")


@router.get(
    "/models/{business_id}",
    response_model=List[schemas.MLModelRead]
)
def list_models(
    business_id: int,
    database: Session = Depends(db.get_db),
    user=Depends(get_current_user),
):
    # Demo models are visible to everyone.
    # Private business models are visible only to their owner.
    get_accessible_business(
        business_id, database, user
    )

    return (
        database.query(models.MLModel)
        .filter(models.MLModel.business_id == business_id)
        .all()
    )
