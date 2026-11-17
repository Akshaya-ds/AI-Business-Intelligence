
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core import db, models
from ..core.auth import get_current_user, get_accessible_business
from ..core.dataset_selector import get_active_or_latest_dataset
from ..core.preprocess import preprocess_file, load_dataframe

import pandas as pd
import os
import joblib

router = APIRouter()


@router.get("/{business_id}")
def get_inventory(
    business_id: int,
    database: Session = Depends(db.get_db),
    user=Depends(get_current_user),
):
    # Verify business access before reading inventory data.
    get_accessible_business(
        business_id, database, user
    )

    ds = get_active_or_latest_dataset(
        business_id, database
    )

    if not ds:
        raise HTTPException(
            status_code=404,
            detail="No dataset found for this business."
        )

    custom_mapping = (
        ds.column_mapping
        if isinstance(ds.column_mapping, dict)
        else None
    )

    try:
        df, resolved_mapping = preprocess_file(
            ds.filepath,
            custom_mapping=custom_mapping
        )

        raw_df = load_dataframe(ds.filepath)

        rename_dict = {
            actual: logical
            for logical, actual in resolved_mapping.items()
            if actual and actual in raw_df.columns
        }

        raw_df = raw_df.rename(columns=rename_dict)

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Could not process dataset: {str(e)}"
        )

    # Identify available information.
    has_stock = "stock" in raw_df.columns
    has_product = "product_name" in df.columns
    has_category = "category" in raw_df.columns

    if has_product:
        group_column = "product_name"
        level = "product"

    elif has_category:
        group_column = "product_name"
        level = "category"

    else:
        return {
            "message": "Inventory grouping information is unavailable.",
            "level": None,
            "has_stock_data": has_stock,
            "items": []
        }

    # Inventory configuration.
    settings = (
        database.query(models.BusinessSettings)
        .filter(
            models.BusinessSettings.business_id == business_id
        )
        .first()
    )

    lead_time_days = (
        settings.lead_time_days
        if settings and settings.lead_time_days
        else 7
    )

    safety_stock = (
        settings.safety_stock
        if settings and settings.safety_stock
        else 10
    )

    items = []

    # Group products or categories.
    for name, group in df.groupby(group_column):

        name = str(name).strip()

        if not name or name.lower() == "nan":
            continue

        category = name if level == "category" else "General"

        product_rows = (
            raw_df[raw_df[group_column] == name]
            if group_column in raw_df.columns
            else pd.DataFrame()
        )

        if not product_rows.empty and "date" in product_rows.columns:
            product_rows = product_rows.copy()
            product_rows["date"] = pd.to_datetime(
                product_rows["date"],
                errors="coerce"
            )
            product_rows = product_rows.sort_values("date")

        latest_row = (
            product_rows.iloc[-1]
            if not product_rows.empty
            else None
        )

        current_stock = None
        unit_price = None

        if latest_row is not None:

            if has_stock and pd.notnull(latest_row.get("stock")):
                current_stock = float(latest_row["stock"])

            if (
                "price" in raw_df.columns
                and pd.notnull(latest_row.get("price"))
            ):
                unit_price = float(latest_row["price"])

            if (
                "category" in raw_df.columns
                and pd.notnull(latest_row.get("category"))
            ):
                category = str(latest_row["category"])

        # Calculate historical demand.
        historical_quantity = (
            float(group["quantity"].sum())
            if "quantity" in group.columns
            else 0.0
        )

        date_count = (
            max(
                1,
                (group["date"].max() - group["date"].min()).days + 1
            )
            if "date" in group.columns
            else 1
        )

        daily_demand = historical_quantity / date_count

        # Forecast only if a trained model exists.
        ml_model = (
            database.query(models.MLModel)
            .filter(
                models.MLModel.business_id == business_id,
                models.MLModel.dataset_id == ds.id,
                models.MLModel.product_name == name
            )
            .order_by(models.MLModel.created_at.desc())
            .first()
        )

        demand_7d = round(daily_demand * 7)
        demand_lead = round(daily_demand * lead_time_days)

        forecast_source = "Historical average"

        if ml_model and os.path.isfile(ml_model.file_path):

            try:
                model = joblib.load(ml_model.file_path)

                min_date = group["date"].min()
                max_date = group["date"].max()

                last_index = (max_date - min_date).days

                prediction_days = max(lead_time_days, 7)

                future_indices = [
                    [last_index + i]
                    for i in range(1, prediction_days + 1)
                ]

                predictions = model.predict(future_indices)

                predictions = [
                    max(0.0, float(value))
                    for value in predictions
                ]

                demand_7d = round(sum(predictions[:7]))
                demand_lead = round(
                    sum(predictions[:lead_time_days])
                )

                daily_demand = (
                    sum(predictions) / len(predictions)
                )

                forecast_source = "ML model"

            except Exception:
                # Fall back to historical demand.
                pass

        reorder_point = demand_lead + safety_stock

        if current_stock is None:

            status = "No Stock Data"
            alert = "Upload stock information to enable inventory monitoring."
            recommended_reorder = None

        elif current_stock <= 0:

            status = "Stockout"
            alert = "Out of stock. Immediate reorder required."
            recommended_reorder = reorder_point

        elif current_stock < safety_stock:

            status = "Critical Low"
            alert = "Stock is below the safety threshold."
            recommended_reorder = max(
                0, reorder_point - current_stock
            )

        elif current_stock < reorder_point:

            status = "Low Stock"
            alert = "Stock is approaching the reorder point."
            recommended_reorder = max(
                0, reorder_point - current_stock
            )

        elif current_stock > reorder_point * 3:

            status = "Excess"
            alert = "Excess inventory detected."
            recommended_reorder = 0

        else:

            status = "Healthy"
            alert = None
            recommended_reorder = 0

        items.append({
            "product_name": name,
            "category": category,
            "level": level,
            "current_stock": current_stock,
            "unit_price": unit_price,
            "daily_demand": round(daily_demand, 2),
            "demand_7d": demand_7d,
            "reorder_point": reorder_point,
            "safety_stock": safety_stock,
            "status": status,
            "alert": alert,
            "recommended_reorder": recommended_reorder,
            "forecast_source": forecast_source
        })

    return {
        "business_id": business_id,
        "dataset_id": ds.id,
        "level": level,
        "has_stock_data": has_stock,
        "lead_time_days": lead_time_days,
        "safety_stock": safety_stock,
        "message": (
            "Inventory data available."
            if has_stock
            else "Sales data available, but stock information is not present."
        ),
        "items": items
    }
