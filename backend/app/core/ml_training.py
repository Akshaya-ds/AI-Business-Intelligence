import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
import joblib
from typing import Dict, Tuple, List

from .preprocess import preprocess_file

def _time_split(df: pd.DataFrame, test_ratio: float = 0.2) -> Tuple[pd.DataFrame, pd.DataFrame]:
    if 'date' in df.columns:
        df = df.sort_values('date')
    cutoff = max(1, int(len(df) * (1 - test_ratio)))
    return df.iloc[:cutoff], df.iloc[cutoff:]

def _evaluate(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    mae = float(mean_absolute_error(y_true, y_pred))
    # root_mean_squared_error is standard across scikit-learn versions
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    mask = y_true != 0
    mape = float(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask]).mean() * 100) if mask.any() else None
    return {"mae": round(mae, 2), "rmse": round(rmse, 2), "mape": round(mape, 2) if mape is not None else None}

def train_product_model(df_product: pd.DataFrame, model_dir: str, product_name: str) -> Tuple[str, Dict[str, float]]:
    if len(df_product) < 10:
        raise ValueError("Not enough data points for training (need >=10).")
    df = df_product.copy().sort_values('date')
    df['day_index'] = (df['date'] - df['date'].min()).dt.days
    
    train_df, test_df = _time_split(df)
    train_X = train_df[['day_index']].values
    train_y = train_df['quantity'].values
    test_X = test_df[['day_index']].values
    test_y = test_df['quantity'].values
    
    # Choose algorithm based on data size
    if len(df) <= 30:
        model = RandomForestRegressor(n_estimators=50, max_depth=3, random_state=42)
    else:
        try:
            from xgboost import XGBRegressor
            model = XGBRegressor(objective='reg:squarederror', n_estimators=100, max_depth=4, learning_rate=0.05, random_state=42)
        except Exception:
            model = RandomForestRegressor(n_estimators=100, random_state=42)
            
    model.fit(train_X, train_y)
    preds = model.predict(test_X)
    metrics = _evaluate(test_y, preds)
    
    os.makedirs(model_dir, exist_ok=True)
    safe_name = "".join(c if c.isalnum() else "_" for c in product_name)
    model_path = os.path.join(model_dir, f"model_{safe_name}.pkl")
    joblib.dump(model, model_path)
    return model_path, metrics

def train_all_products(aggregated_df: pd.DataFrame, model_root: str) -> Dict[str, Dict]:
    results = {}
    for product, group in aggregated_df.groupby('product_name'):
        try:
            path, metrics = train_product_model(group, model_root, str(product))
            results[str(product)] = {"model_path": path, "metrics": metrics}
        except Exception as e:
            results[str(product)] = {"error": str(e)}
    return results
