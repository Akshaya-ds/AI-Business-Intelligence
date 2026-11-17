
import os
import joblib
import pandas as pd

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core import db, models
from ..core.auth import get_current_user, get_accessible_business
from ..core.dataset_selector import get_active_or_latest_dataset
from ..core.preprocess import preprocess_file

from datetime import timedelta

router = APIRouter()

def _load_latest_model(
    business_id: int,
    product_name: str,
    dataset_id: int,
    database: Session
):
    model_rec = (
        database.query(models.MLModel)
        .filter(
            models.MLModel.business_id == business_id,
            models.MLModel.product_name == product_name,
            models.MLModel.dataset_id == dataset_id
        )
        .order_by(models.MLModel.created_at.desc())
        .first()
    )

    if not model_rec:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No trained ML model found for '{product_name}' "
                "in the currently selected dataset. "
                "Please train models for this dataset in the ML Training tab."
            )
        )

    if not os.path.isfile(model_rec.file_path):
        raise HTTPException(
            status_code=500,
            detail="Trained model artifact is missing from server storage."
        )

    return model_rec, joblib.load(model_rec.file_path)

@router.get(
    "/forecast/{business_id}/{product_name}",
    response_model=dict
)
def forecast_product(
    business_id: int,
    product_name: str,
    days: int = 7,
    database: Session = Depends(db.get_db),
    user=Depends(get_current_user),
):
    # Verify access before reading the dataset or model.
    get_accessible_business(
        business_id, database, user
    )

    dataset = get_active_or_latest_dataset(
        business_id, database
    )

    model_rec, model = _load_latest_model(
        business_id,
        product_name,
        dataset.id,
        database
    )

    mapping = (
        dataset.column_mapping
        if isinstance(dataset.column_mapping, dict)
        else None
    )

    try:
        agg_df, _ = preprocess_file(
            dataset.filepath,
            custom_mapping=mapping
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Could not process dataset for forecasting: {str(e)}"
        )

    prod_df = (
        agg_df[agg_df["product_name"] == product_name]
        .sort_values("date")
    )

    if prod_df.empty:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No historical sales data found for '{product_name}' "
                "in the selected dataset."
            )
        )

    # Check minimum history.
    if len(prod_df) < 5:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Insufficient historical records for '{product_name}' "
                f"({len(prod_df)} days found, need >= 5)."
            )
        )

    min_date = prod_df["date"].min()
    max_date = prod_df["date"].max()

    day_index_start = (max_date - min_date).days

    # Predict exactly into the future starting strictly AFTER max_date.
    future_indices = [
        [day_index_start + i]
        for i in range(1, days + 1)
    ]

    try:
        preds = model.predict(future_indices)

    except Exception:
        # Fallback to moving average if prediction encounters a dimension issue.
        avg_q = max(
            1.0,
            float(prod_df["quantity"].tail(14).mean())
        )
        preds = [avg_q] * days

    forecast_dates = [
        (max_date + timedelta(days=i)).date().isoformat()
        for i in range(1, days + 1)
    ]

    # Return last 14 historical points for chart context.
    history_slice = prod_df.tail(14)

    recent_history = [
        {
            "date": d.strftime("%Y-%m-%d"),
            "quantity": int(round(q))
        }
        for d, q in zip(
            history_slice["date"],
            history_slice["quantity"]
        )
    ]

    return {
        "product": product_name,
        "dataset_name": dataset.filename,
        "last_historical_date": max_date.strftime("%Y-%m-%d"),
        "forecast_start_date": (
            forecast_dates[0] if forecast_dates else None
        ),
        "forecast_end_date": (
            forecast_dates[-1] if forecast_dates else None
        ),
        "horizon_days": days,
        "model_type": model_rec.model_type,
        "metrics": model_rec.metrics,
        "history": recent_history,
        "forecast": [
            {
                "date": d,
                "quantity": max(0, int(round(float(q))))
            }
            for d, q in zip(forecast_dates, preds)
        ]
    }