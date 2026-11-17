from pydantic import BaseModel, EmailStr, ConfigDict, Field
from typing import Optional, List, Dict, Any

# Base configuration for ORM mode (Pydantic v2) with protected namespaces cleared
class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

class BusinessCreate(ORMModel):
    name: str = Field(..., example="Acme Corp")
    type: Optional[str] = Field(None, example="Retail")
    description: Optional[str] = Field(None, example="A leading retailer of widgets.")
    contact_email: Optional[EmailStr] = Field(None, example="admin@acme.com")

class BusinessRead(ORMModel):
    id: int
    name: str
    type: Optional[str]
    description: Optional[str]
    contact_email: Optional[EmailStr]
    created_at: Any

class MLModelRead(ORMModel):
    id: int
    business_id: int
    dataset_id: int
    product_name: str
    model_type: str
    metrics: Optional[Dict[str, Any]] = None
    file_path: str
    created_at: Any

class BusinessSettingsSchema(ORMModel):
    id: int
    business_id: int
    active_dataset_id: Optional[int] = None
    lead_time_days: Optional[int] = None
    safety_stock: Optional[int] = None
    total_revenue: Optional[float] = None
    total_units_sold: Optional[int] = None
    number_of_products: Optional[int] = None
    total_transactions: Optional[int] = None
    profit: Optional[float] = None
    profit_margin: Optional[float] = None

class DatasetMeta(ORMModel):
    id: int
    business_id: int
    filename: str
    uploaded_at: Any
    column_names: Optional[List[str]] = None
    column_mapping: Optional[Dict[str, Optional[str]]] = None
    row_count: Optional[int] = None
    has_date: int
    has_product_name: int
    has_category: int
    has_quantity: int
    has_price: int
    has_cost: int
    has_revenue: int
    has_stock: int
    is_active: Optional[bool] = False

class DatasetUploadResponse(ORMModel):
    dataset: DatasetMeta
    preview: List[Dict[str, Any]]
    detected_mapping: Optional[Dict[str, Optional[str]]] = None

class AnalyticsSummary(ORMModel):
    total_transactions: Optional[int] = None
    number_of_products: Optional[int] = None
    total_revenue: Optional[float] = None
    total_units_sold: Optional[int] = None
    profit: Optional[float] = None
    profit_margin: Optional[float] = None
    dataset_filename: Optional[str] = None

class TimeSeriesPoint(ORMModel):
    date: str
    revenue: Optional[float] = None
    units_sold: Optional[int] = None

class TimeSeriesResponse(ORMModel):
    points: List[TimeSeriesPoint]

class TopProduct(ORMModel):
    product_name: str
    revenue: float
    units_sold: int

class CategoryPerformance(ORMModel):
    category: str
    revenue: float
    units_sold: int
