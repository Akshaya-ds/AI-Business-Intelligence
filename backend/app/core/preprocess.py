
import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
import os


COMMON_COLUMNS = {
    "date": [
        "date", "order_date", "sale_date", "transaction_date",
        "invoice_date", "time", "day", "order date",
        "sale date", "datetime", "timestamp"
    ],
    "product_name": [
        "product name", "product_name", "product", "item",
        "item_name", "product_id", "sku", "item name"
    ],
    "category": [
        "product category", "product_category", "category",
        "type", "department", "segment", "product type",
        "item category", "itemcategory"
    ],
    "quantity": [
        "quantity sold", "quantity_sold", "qty", "quantity",
        "units", "units_sold", "units sold", "volume"
    ],
    "price": [
        "selling price", "selling_price", "price",
        "unit price", "unit_price", "sales_price", "rate"
    ],
    "cost": [
        "cost price", "cost_price", "cost",
        "unit cost", "unit_cost", "cogs", "buy_price"
    ],
    "revenue": [
        "revenue", "sales", "total", "total_sales",
        "amount", "total_amount", "totalamount",
        "line_total", "total price"
    ],
    "stock": [
        "available stock", "available_stock", "stock",
        "inventory", "current_stock", "quantity_on_hand",
        "qty_on_hand", "stock_level"
    ],
    "store": [
        "store", "store_name", "store location",
        "branch", "branch_name"
    ],
    "invoice_id": [
        "invoice", "invoice_no", "invoiceno",
        "invoice_id", "transaction_id", "order_id"
    ],
    "payment_method": [
        "payment_method", "payment method",
        "paymentmethod", "payment_type"
    ]
}


def _normalize(col: str) -> str:
    return (
        str(col).strip().lower()
        .replace("_", " ")
        .replace("-", " ")
    )


def detect_columns(df: pd.DataFrame) -> Dict[str, Optional[str]]:

    mapping = {key: None for key in COMMON_COLUMNS}

    cols_normalized = {
        _normalize(c): c for c in df.columns
    }

    for logical, variants in COMMON_COLUMNS.items():

        for variant in variants:
            normalized = _normalize(variant)

            if normalized in cols_normalized:
                mapping[logical] = cols_normalized[normalized]
                break

    return mapping


def load_dataframe(filepath: str) -> pd.DataFrame:

    ext = os.path.splitext(filepath)[1].lower()

    if ext == ".csv":

        try:
            df = pd.read_csv(filepath, sep=None, engine="python")
        except UnicodeDecodeError:
            df = pd.read_csv(
                filepath,
                sep=None,
                engine="python",
                encoding="latin1"
            )

        return df

    elif ext in (".xlsx", ".xls"):
        return pd.read_excel(filepath)

    else:
        raise ValueError(
            f"Unsupported file format '{ext}'. "
            "Upload CSV, XLSX or XLS."
        )


def apply_mapping(
    df: pd.DataFrame,
    mapping: Dict[str, Optional[str]]
) -> pd.DataFrame:

    df_copy = df.copy()

    rename_dict = {
        actual: logical
        for logical, actual in mapping.items()
        if actual and actual in df_copy.columns
    }

    df_copy = df_copy.rename(columns=rename_dict)

    # Calculate revenue when it is not supplied.
    if (
        "revenue" not in df_copy.columns
        and "price" in df_copy.columns
        and "quantity" in df_copy.columns
    ):
        price = pd.to_numeric(
            df_copy["price"], errors="coerce"
        )

        quantity = pd.to_numeric(
            df_copy["quantity"], errors="coerce"
        )

        df_copy["revenue"] = price * quantity

    return df_copy


def clean_data(df: pd.DataFrame) -> pd.DataFrame:

    df = df.copy()
    df = df.drop_duplicates()

    if "date" in df.columns:
        df["date"] = pd.to_datetime(
            df["date"], errors="coerce"
        )

        df = df.dropna(subset=["date"])

    for col in ["product_name", "category", "store",
                "payment_method"]:

        if col in df.columns:
            df[col] = df[col].astype("string").str.strip()
            df[col] = df[col].replace("", pd.NA)

    numeric_cols = [
        "quantity", "price", "cost", "revenue", "stock"
    ]

    for col in numeric_cols:
        if col in df.columns:
            # Also handle currency symbols and commas.
            values = (
                df[col].astype(str)
                .str.replace(",", "", regex=False)
                .str.replace("₹", "", regex=False)
                .str.replace("$", "", regex=False)
                .str.strip()
            )

            df[col] = pd.to_numeric(
                values, errors="coerce"
            )

    return df


def aggregate_sales(df: pd.DataFrame) -> pd.DataFrame:

    if "date" not in df.columns:
        raise ValueError(
            "A date column is required for time-based analytics."
        )

    if "quantity" not in df.columns:
        raise ValueError(
            "A quantity column is required for sales analytics."
        )

    # Prefer actual product names.
    # If unavailable, use category for category-level analysis.
    if "product_name" in df.columns:
        group_column = "product_name"
        aggregation_level = "product"

    elif "category" in df.columns:
        group_column = "category"
        aggregation_level = "category"

    else:
        raise ValueError(
            "This dataset has no Product Name or Category column. "
            "Please provide one for product/category analytics."
        )

    aggregation = {
        "quantity": "sum"
    }

    if "revenue" in df.columns:
        aggregation["revenue"] = "sum"

    if "price" in df.columns:
        aggregation["price"] = "mean"

    if "cost" in df.columns:
        aggregation["cost"] = "mean"

    group_columns = ["date", group_column]

    # Keep additional business dimensions where available.
    for col in ["store", "payment_method"]:
        if col in df.columns:
            group_columns.append(col)

    agg = (
        df.groupby(group_columns, dropna=False)
        .agg(aggregation)
        .reset_index()
    )

    # Provide a consistent key for existing analytics/ML APIs.
    if group_column == "category":
        agg = agg.rename(columns={"category": "product_name"})

    agg["aggregation_level"] = aggregation_level

    agg = agg.sort_values("date").reset_index(drop=True)

    return agg


def preprocess_file(
    filepath: str,
    custom_mapping: Optional[
        Dict[str, Optional[str]]
    ] = None
) -> Tuple[pd.DataFrame, Dict[str, Optional[str]]]:

    raw = load_dataframe(filepath)

    if raw.empty:
        raise ValueError("The uploaded dataset is empty.")

    detected_mapping = detect_columns(raw)

    mapping = detected_mapping.copy()

    if custom_mapping:
        for logical, actual in custom_mapping.items():

            if actual and actual in raw.columns:
                mapping[logical] = actual

    df = apply_mapping(raw, mapping)

    df = clean_data(df)

    if df.empty:
        raise ValueError(
            "No valid records remain after cleaning the dataset."
        )

    agg = aggregate_sales(df)

    return agg, mapping
