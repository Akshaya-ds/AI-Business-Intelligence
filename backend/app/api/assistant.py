
import os
import joblib
import pandas as pd

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..core import db, models
from ..core.auth import get_current_user, get_accessible_business
from ..core.dataset_selector import get_active_or_latest_dataset
from ..core.preprocess import preprocess_file, load_dataframe

router = APIRouter()

class ChatRequest(BaseModel):
    question: str

def build_business_context(
    business_id: int,
    database: Session
):

    # Get active or latest dataset.
    ds = get_active_or_latest_dataset(
        business_id, database
    )

    if not ds:
        raise ValueError("No dataset found for this business.")

    custom_mapping = (
        ds.column_mapping
        if isinstance(ds.column_mapping, dict)
        else None
    )

    # Process dataset.
    df, resolved_mapping = preprocess_file(
        ds.filepath,
        custom_mapping=custom_mapping
    )

    # Load original dataset.
    raw_df = load_dataframe(ds.filepath)

    raw_df = raw_df.rename(columns={
        actual: logical
        for logical, actual in resolved_mapping.items()
        if actual and actual in raw_df.columns
    })

    if "product_name" not in raw_df.columns:
        raise ValueError("Product name column is missing.")

    raw_df["product_name"] = (
        raw_df["product_name"].astype(str).str.strip()
    )

    if "product_name" in df.columns:
        df["product_name"] = (
            df["product_name"].astype(str).str.strip()
        )

    if "date" in raw_df.columns:
        raw_df["date"] = pd.to_datetime(
            raw_df["date"], errors="coerce"
        )
        raw_df = raw_df.sort_values("date")

    if "date" in df.columns:
        df["date"] = pd.to_datetime(
            df["date"], errors="coerce"
        )

    has_stock = "stock" in raw_df.columns

    # Business inventory settings.
    settings = database.query(
        models.BusinessSettings
    ).filter(
        models.BusinessSettings.business_id == business_id
    ).first()

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

    # Business performance calculations.
    if "revenue" in raw_df.columns:

        raw_df["revenue"] = pd.to_numeric(
            raw_df["revenue"],
            errors="coerce"
        ).fillna(0)

        total_revenue = float(
            raw_df["revenue"].sum()
        )

        product_revenue = (
            raw_df.groupby("product_name")["revenue"]
            .sum()
            .to_dict()
        )

    else:
        total_revenue = 0.0
        product_revenue = {}

    quantity = (
        pd.to_numeric(
            df["quantity"],
            errors="coerce"
        ).fillna(0)
        if "quantity" in df.columns
        else pd.Series(dtype=float)
    )

    total_units = float(quantity.sum())
    transactions = len(raw_df)

    # Fetch models for exact business and dataset.
    trained_models = database.query(
        models.MLModel
    ).filter(
        models.MLModel.business_id == business_id,
        models.MLModel.dataset_id == ds.id
    ).all()

    model_lookup = {
        record.product_name: record
        for record in trained_models
    }

    inventory_items = []

    # Inventory calculations.
    for product, group in df.groupby("product_name"):

        product = str(product).strip()
        group = group.sort_values("date")

        product_rows = raw_df[
            raw_df["product_name"] == product
        ]

        latest_row = (
            product_rows.iloc[-1]
            if not product_rows.empty
            else None
        )

        current_stock = None
        category = "General"
        unit_price = None

        if latest_row is not None:

            if (
                has_stock
                and pd.notnull(latest_row.get("stock"))
            ):
                try:
                    current_stock = int(
                        float(latest_row["stock"])
                    )
                except (ValueError, TypeError):
                    current_stock = None

            if (
                "category" in raw_df.columns
                and pd.notnull(latest_row.get("category"))
            ):
                category = str(
                    latest_row["category"]
                )

            if (
                "price" in raw_df.columns
                and pd.notnull(latest_row.get("price"))
            ):
                try:
                    unit_price = float(
                        latest_row["price"]
                    )
                except (ValueError, TypeError):
                    unit_price = None

        # Find exact product model.
        ml_model = model_lookup.get(product)

        daily_demand = None
        demand_7d = None
        reorder_point = None
        status = "No Model Data"
        alert = "A trained model is not available."
        recommended_reorder = None
        model_mae = None
        model_type = None

        if ml_model:

            model_metrics = ml_model.metrics or {}

            model_mae = model_metrics.get("MAE")

            if model_mae is None:
                model_mae = model_metrics.get("mae")

            model_type = ml_model.model_type

            if os.path.isfile(ml_model.file_path):

                try:
                    trained_model = joblib.load(
                        ml_model.file_path
                    )

                    min_date = group["date"].min()
                    max_date = group["date"].max()

                    if pd.isna(min_date) or pd.isna(max_date):
                        raise ValueError(
                            "Valid product dates are unavailable."
                        )

                    last_index = (
                        max_date - min_date
                    ).days

                    prediction_days = max(
                        lead_time_days, 7
                    )

                    future_indices = [
                        [last_index + i]
                        for i in range(
                            1, prediction_days + 1
                        )
                    ]

                    predictions = trained_model.predict(
                        future_indices
                    )

                    predictions = [
                        max(0.0, float(value))
                        for value in predictions
                    ]

                    daily_demand = round(
                        sum(predictions) / len(predictions),
                        1
                    )

                    demand_7d = round(
                        sum(predictions[:7])
                    )

                    forecast_demand_lead = round(
                        sum(
                            predictions[:lead_time_days]
                        )
                    )

                    # Reorder point.
                    reorder_point = (
                        forecast_demand_lead + safety_stock
                    )

                    # Inventory status.
                    if not has_stock:
                        status = "No Stock Data"
                        alert = (
                            "Dataset does not contain "
                            "a stock column."
                        )

                    elif current_stock is None:
                        status = "No Stock Data"
                        alert = (
                            "Stock information is missing."
                        )

                    elif current_stock <= 0:
                        status = "Stockout"
                        alert = (
                            "Out of stock! Immediate reorder required."
                        )
                        recommended_reorder = reorder_point

                    elif current_stock < safety_stock:
                        status = "Critical Low"
                        alert = (
                            f"Stock ({current_stock}) is below "
                            f"safety threshold ({safety_stock})."
                        )
                        recommended_reorder = max(
                            0,
                            reorder_point - current_stock
                        )

                    elif current_stock < reorder_point:
                        status = "Low Stock"
                        alert = (
                            f"Approaching reorder point "
                            f"({reorder_point} units)."
                        )
                        recommended_reorder = (
                            reorder_point - current_stock
                        )

                    elif current_stock > reorder_point * 3:
                        status = "Excess"
                        alert = (
                            "Excess inventory detected above "
                            "normal buffer."
                        )
                        recommended_reorder = 0

                    else:
                        status = "Healthy"
                        alert = "Stock level is healthy."
                        recommended_reorder = 0

                except Exception as error:
                    status = "Calculation Error"
                    alert = str(error)

            else:
                status = "Model File Missing"
                alert = "Trained model file is unavailable."

        inventory_items.append({
            "product_name": product,
            "category": category,
            "current_stock": current_stock,
            "unit_price": unit_price,
            "daily_demand": daily_demand,
            "demand_7d": demand_7d,
            "reorder_point": reorder_point,
            "safety_stock": safety_stock,
            "status": status,
            "alert": alert,
            "recommended_reorder": recommended_reorder,
            "model_type": model_type,
            "model_mae": model_mae,
            "total_revenue": round(
                float(product_revenue.get(product, 0)),
                2
            )
        })

    # Sort products by revenue.
    top_products = sorted(
        inventory_items,
        key=lambda item: item["total_revenue"],
        reverse=True
    )

    return {
        "dataset_name": os.path.basename(ds.filepath),
        "dataset_id": ds.id,
        "transactions": transactions,
        "total_revenue": round(total_revenue, 2),
        "total_units_sold": round(total_units, 2),
        "lead_time_days": lead_time_days,
        "safety_stock": safety_stock,
        "top_products": top_products,
        "inventory": inventory_items
    }

def local_answer(question: str, context: dict):

    q = question.lower()
    inventory = context["inventory"]

    # Business performance.
    if (
        any(word in q for word in [
            "analyze", "analysis", "performance", "business"
        ])
        and any(word in q for word in [
            "revenue", "sales", "product"
        ])
    ):

        result = (
            f"Total Revenue: {context['total_revenue']}\n"
            f"Total Units Sold: {context['total_units_sold']}\n"
            f"Transactions: {context['transactions']}\n\n"
            "Top 3 Products by Revenue:\n"
        )

        for index, item in enumerate(
            context["top_products"][:3], 1
        ):
            result += (
                f"{index}. {item['product_name']}: "
                f"{item['total_revenue']}\n"
            )

        return result

    # Inventory analysis.
    if any(word in q for word in [
        "inventory", "stock", "reorder",
        "restock", "shortage"
    ]):

        result = "Inventory Analysis:\n\n"

        for item in inventory:

            result += (
                f"Product: {item['product_name']}\n"
                f"Current Stock: {item['current_stock']}\n"
                f"Daily Demand: {item['daily_demand']}\n"
                f"7-Day Demand: {item['demand_7d']}\n"
                f"Reorder Point: {item['reorder_point']}\n"
                f"Status: {item['status']}\n"
                f"Recommended Reorder: "
                f"{item['recommended_reorder']}\n\n"
            )

        return result

    if "revenue" in q or "sales" in q:
        return (
            f"Total Revenue: {context['total_revenue']}\n"
            f"Total Units Sold: {context['total_units_sold']}"
        )

    if "top" in q or "best" in q:

        result = "Top Products by Revenue:\n"

        for index, item in enumerate(
            context["top_products"][:3], 1
        ):
            result += (
                f"{index}. {item['product_name']} - "
                f"{item['total_revenue']}\n"
            )

        return result

    return (
        "Your latest business dataset is loaded. "
        "Ask about revenue, product performance, "
        "inventory, stock levels, or reorder recommendations."
    )

@router.post("/{business_id}")
def ask_assistant(
    business_id: int,
    request: ChatRequest,
    database: Session = Depends(db.get_db),
    user=Depends(get_current_user),
):

    # Verify access before reading business data.
    get_accessible_business(
        business_id, database, user
    )

    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Please enter a question."
        )

    try:
        context = build_business_context(
            business_id,
            database
        )

    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Could not prepare business data: {str(error)}"
            )
        )

    gemini_key = os.getenv("GEMINI_API_KEY")

    # Local response if Gemini key is unavailable.
    if not gemini_key:
        return {
            "answer": local_answer(question, context),
            "grounded_data": context,
            "gemini_active": False
        }

    try:
        import google.generativeai as genai

        genai.configure(api_key=gemini_key)

        ai_model = genai.GenerativeModel(
            "gemini-3.1-flash-lite"
        )

        prompt = f"""
You are an AI Business Intelligence Assistant.

Answer the user's question using ONLY the provided business data.

BUSINESS DATA:
{context}

IMPORTANT RULES:

1. Use only the supplied business data.
2. Never invent missing stock, demand, revenue or forecast values.
3. If a value is None, clearly say that it is unavailable.
4. Use only the active/latest selected dataset provided.
5. Never mix data from another business or an older dataset.
6. Use actual current stock, daily demand, reorder point,
   inventory status and recommended reorder quantity
   for inventory decisions.
7. Rank restocking urgency using actual inventory status
   and recommended reorder quantity.
8. MAE is a model prediction error metric.
   It is NOT daily demand and NOT an inventory urgency score.
9. Explain recommendations using actual numerical values.
10. Do not assume a currency if the dataset does not specify one.
11. Keep the answer structured and easy to understand.
12. If asked for five products, include all five.
13. Do not recommend a 30-day supply unless the supplied data
    explicitly supports that recommendation.

USER QUESTION:
{question}

Give a clear, data-grounded response.
"""

        response = ai_model.generate_content(prompt)

        answer = (
            response.text
            if response and response.text
            else "I could not generate a response."
        )

        return {
            "answer": answer,
            "grounded_data": context,
            "gemini_active": True
        }

    except Exception as error:

        return {
            "answer": (
                "Gemini connection error: "
                f"{str(error)}\n\n"
                "Local result:\n"
                f"{local_answer(question, context)}"
            ),
            "grounded_data": context,
            "gemini_active": False
        }