import pandas as pd
import os
from typing import List, Dict, Any

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

def _detect_columns(df: pd.DataFrame) -> dict:
    cols = [c.lower() for c in df.columns]
    return {
        "has_date": int(any('date' in c for c in cols)),
        "has_product_name": int(any('product' in c and 'name' in c for c in cols)),
        "has_category": int(any('category' in c for c in cols)),
        "has_quantity": int(any('quantity' in c or 'qty' in c for c in cols)),
        "has_price": int(any('price' in c for c in cols)),
        "has_cost": int(any('cost' in c for c in cols)),
        "has_revenue": int(any('revenue' in c for c in cols)),
        "has_stock": int(any('stock' in c for c in cols)),
        "columns": list(df.columns),
        "row_count": len(df),
    }

def validate_and_preview(file_path: str, preview_rows: int = 10) -> (dict, List[Dict[str, Any]]):
    # size check
    if os.path.getsize(file_path) > MAX_FILE_SIZE:
        raise ValueError("File exceeds maximum allowed size of 50 MB")
    # read file based on extension
    ext = os.path.splitext(file_path)[1].lower()
    try:
        if ext == ".csv":
            df = pd.read_csv(file_path)
        elif ext in (".xlsx", ".xls"):
            df = pd.read_excel(file_path)
        else:
            raise ValueError("Unsupported file format")
    except Exception as e:
        raise ValueError(f"Error reading file: {e}")
    # basic checks
    if df.empty:
        raise ValueError("Uploaded file contains no data")
    # duplicate rows check (just warn, not error)
    if df.duplicated().any():
        # we allow duplicates but could log; for now just continue
        pass
    # missing values info – we don't reject, just note
    meta = _detect_columns(df)
    preview = df.head(preview_rows).to_dict(orient="records")
    return meta, preview

def get_preview(file_path: str, rows: int = 20) -> List[Dict[str, Any]]:
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".csv":
        df = pd.read_csv(file_path, nrows=rows)
    elif ext in (".xlsx", ".xls"):
        df = pd.read_excel(file_path, nrows=rows)
    else:
        raise ValueError("Unsupported file format")
    return df.to_dict(orient="records")
