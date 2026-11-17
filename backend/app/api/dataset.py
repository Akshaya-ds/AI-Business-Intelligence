
import os
from typing import List

from fastapi import (
    APIRouter, Depends, UploadFile, File, HTTPException
)
from sqlalchemy.orm import Session

from ..core import db, models, schemas
from ..core.auth import get_current_user, get_accessible_business
from ..utils.file_handler import save_upload_file
from ..core import upload as upload_utils

router = APIRouter()


@router.post(
    "/{business_id}",
    response_model=schemas.DatasetUploadResponse
)
async def upload_dataset(
    business_id: int,
    file: UploadFile = File(...),
    database: Session = Depends(db.get_db),
    user=Depends(get_current_user),
):
    # Verify that the user can access this business.
    business = get_accessible_business(
        business_id, database, user
    )

    # Public Demo is read-only.
    if business.is_public:
        raise HTTPException(
            status_code=403,
            detail="The public Demo business is read-only. Dataset uploads are disabled."
        )

    # Validate file type.
    filename = file.filename or ""

    if not filename.lower().endswith((".csv", ".xlsx")):
        raise HTTPException(
            status_code=400,
            detail="Only CSV and Excel files are supported."
        )

    # Save file safely.
    saved_path = save_upload_file(file)

    # Validate and extract preview and metadata.
    try:
        meta, preview = upload_utils.validate_and_preview(
            saved_path
        )
    except ValueError as e:
        if os.path.isfile(saved_path):
            os.remove(saved_path)

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception:
        if os.path.isfile(saved_path):
            os.remove(saved_path)

        raise HTTPException(
            status_code=400,
            detail="Could not read the uploaded dataset."
        )

    # Persist dataset record.
    try:
        dataset = models.Dataset(
            business_id=business_id,
            filename=filename,
            filepath=saved_path,
            column_names=meta.get("columns"),
            row_count=meta.get("row_count"),
            has_date=meta.get("has_date", 0),
            has_product_name=meta.get("has_product_name", 0),
            has_category=meta.get("has_category", 0),
            has_quantity=meta.get("has_quantity", 0),
            has_price=meta.get("has_price", 0),
            has_cost=meta.get("has_cost", 0),
            has_revenue=meta.get("has_revenue", 0),
            has_stock=meta.get("has_stock", 0),
        )

        database.add(dataset)
        database.commit()
        database.refresh(dataset)

    except Exception:
        database.rollback()

        if os.path.isfile(saved_path):
            os.remove(saved_path)

        raise HTTPException(
            status_code=500,
            detail="Could not save the dataset."
        )

    return schemas.DatasetUploadResponse(
        dataset=schemas.DatasetMeta.model_validate(dataset),
        preview=preview,
    )


@router.get(
    "/{business_id}",
    response_model=List[schemas.DatasetMeta]
)
def list_datasets(
    business_id: int,
    database: Session = Depends(db.get_db),
    user=Depends(get_current_user),
):
    # Public Demo datasets can be viewed by everyone.
    # Private business datasets require the owner's login.
    get_accessible_business(
        business_id, database, user
    )

    datasets = (
        database.query(models.Dataset)
        .filter(models.Dataset.business_id == business_id)
        .order_by(models.Dataset.uploaded_at.desc())
        .all()
    )

    return [
        schemas.DatasetMeta.model_validate(dataset)
        for dataset in datasets
    ]


@router.get(
    "/preview/{dataset_id}",
    response_model=List[dict]
)
def preview_dataset(
    dataset_id: int,
    database: Session = Depends(db.get_db),
    user=Depends(get_current_user),
):
    dataset = (
        database.query(models.Dataset)
        .filter(models.Dataset.id == dataset_id)
        .first()
    )

    if not dataset:
        raise HTTPException(
            status_code=404,
            detail="Dataset not found"
        )

    # Check access through the dataset's parent business.
    get_accessible_business(
        dataset.business_id,
        database,
        user
    )

    if not os.path.isfile(dataset.filepath):
        raise HTTPException(
            status_code=404,
            detail="Dataset file is missing from server storage."
        )

    # Return first 20 rows as list of dictionaries.
    preview = upload_utils.get_preview(
        dataset.filepath,
        rows=20
    )

    return preview
