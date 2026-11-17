from sqlalchemy.orm import Session
from ..core import models
import os
from fastapi import HTTPException

def get_active_or_latest_dataset(business_id: int, db: Session) -> models.Dataset:
    # 1. Check if an active dataset is configured in BusinessSettings
    settings = db.query(models.BusinessSettings).filter(models.BusinessSettings.business_id == business_id).first()
    if settings and settings.active_dataset_id:
        ds = db.query(models.Dataset).filter(
            models.Dataset.id == settings.active_dataset_id,
            models.Dataset.business_id == business_id
        ).first()
        if ds and os.path.isfile(ds.filepath):
            return ds
            
    # 2. Fall back to latest uploaded dataset for this business
    ds = (
        db.query(models.Dataset)
        .filter(models.Dataset.business_id == business_id)
        .order_by(models.Dataset.uploaded_at.desc())
        .first()
    )
    if not ds:
        raise HTTPException(status_code=404, detail="No dataset found for this business. Please upload a dataset first.")
    if not os.path.isfile(ds.filepath):
        raise HTTPException(status_code=404, detail=f"Dataset file '{ds.filename}' is missing from server storage.")
    return ds
