import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime
from .preprocess import load_dataframe, detect_columns, apply_mapping, clean_data

def get_mapped_df(filepath: str, custom_mapping: Optional[Dict[str, Optional[str]]] = None) -> pd.DataFrame:
    raw = load_dataframe(filepath)
    mapping = custom_mapping if custom_mapping else detect_columns(raw)
    df = apply_mapping(raw, mapping)
    df = clean_data(df)
    return df

def compute_summary(filepath: str, custom_mapping: Optional[Dict[str, Optional[str]]] = None) -> Dict[str, Any]:
    df = get_mapped_df(filepath, custom_mapping)
    
    total_tx = int(len(df))
    num_products = int(df['product_name'].nunique()) if 'product_name' in df.columns else None
    
    result = {
        'total_transactions': total_tx,
        'number_of_products': num_products,
        'total_revenue': 0.0,
        'total_units_sold': 0,
        'profit': None,
        'profit_margin': None
    }
    
    if 'revenue' in df.columns:
        result['total_revenue'] = float(round(df['revenue'].sum(), 2))
    elif 'price' in df.columns and 'quantity' in df.columns:
        result['total_revenue'] = float(round((df['price'] * df['quantity']).sum(), 2))
        
    if 'quantity' in df.columns:
        result['total_units_sold'] = int(round(df['quantity'].sum()))
        
    if 'cost' in df.columns and 'revenue' in df.columns and df['cost'].sum() > 0:
        profit = float(df['revenue'].sum() - df['cost'].sum())
        result['profit'] = round(profit, 2)
        if df['revenue'].sum() > 0:
            result['profit_margin'] = round(profit / df['revenue'].sum(), 4)
            
    return result

def sales_trend(filepath: str, custom_mapping: Optional[Dict[str, Optional[str]]] = None) -> List[Dict[str, Any]]:
    df = get_mapped_df(filepath, custom_mapping)
    if 'date' not in df.columns or df['date'].empty:
        return []
        
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    # Group by date
    daily = df.groupby(df['date'].dt.strftime('%Y-%m-%d')).agg(
        revenue=('revenue', 'sum') if 'revenue' in df.columns else ('date', 'count'),
        units_sold=('quantity', 'sum') if 'quantity' in df.columns else ('date', 'count')
    ).reset_index().rename(columns={'index': 'date'})
    
    points = []
    for _, row in daily.iterrows():
        points.append({
            'date': str(row['date']),
            'revenue': round(float(row['revenue']), 2) if 'revenue' in df.columns else 0.0,
            'units_sold': int(round(row['units_sold'])) if 'quantity' in df.columns else 0
        })
    return points

def top_products(filepath: str, n: int = 10, custom_mapping: Optional[Dict[str, Optional[str]]] = None) -> List[Dict[str, Any]]:
    df = get_mapped_df(filepath, custom_mapping)
    if 'product_name' not in df.columns:
        return []
        
    rev_col = 'revenue' if 'revenue' in df.columns else None
    qty_col = 'quantity' if 'quantity' in df.columns else None
    
    grouped = df.groupby('product_name').agg(
        revenue=(rev_col, 'sum') if rev_col else ('product_name', 'count'),
        units_sold=(qty_col, 'sum') if qty_col else ('product_name', 'count')
    ).reset_index()
    
    if rev_col:
        grouped = grouped.sort_values('revenue', ascending=False)
    else:
        grouped = grouped.sort_values('units_sold', ascending=False)
        
    top = grouped.head(n)
    return [
        {
            'product_name': str(r['product_name']),
            'revenue': round(float(r['revenue']), 2) if rev_col else 0.0,
            'units_sold': int(round(r['units_sold'])) if qty_col else 0
        }
        for _, r in top.iterrows()
    ]

def category_performance(filepath: str, custom_mapping: Optional[Dict[str, Optional[str]]] = None) -> List[Dict[str, Any]]:
    df = get_mapped_df(filepath, custom_mapping)
    if 'category' not in df.columns:
        return []
        
    rev_col = 'revenue' if 'revenue' in df.columns else None
    qty_col = 'quantity' if 'quantity' in df.columns else None
    
    grouped = df.groupby('category').agg(
        revenue=(rev_col, 'sum') if rev_col else ('category', 'count'),
        units_sold=(qty_col, 'sum') if qty_col else ('category', 'count')
    ).reset_index()
    
    if rev_col:
        grouped = grouped.sort_values('revenue', ascending=False)
    else:
        grouped = grouped.sort_values('units_sold', ascending=False)
        
    return [
        {
            'category': str(r['category']),
            'revenue': round(float(r['revenue']), 2) if rev_col else 0.0,
            'units_sold': int(round(r['units_sold'])) if qty_col else 0
        }
        for _, r in grouped.iterrows()
    ]
