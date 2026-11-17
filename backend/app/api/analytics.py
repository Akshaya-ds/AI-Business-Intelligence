
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..core import db, models, schemas, analytics_engine
from ..core.auth import get_current_user, get_accessible_business
from ..core.dataset_selector import get_active_or_latest_dataset

router = APIRouter()


def _get_dataset(business_id: int, database: Session):
    return get_active_or_latest_dataset(
        business_id, database
    )


@router.get(
    "/summary/{business_id}",
    response_model=schemas.AnalyticsSummary
)
def get_summary(
    business_id: int,
    database: Session = Depends(db.get_db),
    user=Depends(get_current_user),
):
    get_accessible_business(
        business_id, database, user
    )

    ds = _get_dataset(business_id, database)

    mapping = (
        ds.column_mapping
        if isinstance(ds.column_mapping, dict)
        else None
    )

    summary = analytics_engine.compute_summary(
        ds.filepath, mapping
    )

    summary["dataset_filename"] = ds.filename

    return schemas.AnalyticsSummary(**summary)


@router.get(
    "/sales-trend/{business_id}",
    response_model=schemas.TimeSeriesResponse
)
def get_sales_trend(
    business_id: int,
    database: Session = Depends(db.get_db),
    user=Depends(get_current_user),
):
    get_accessible_business(
        business_id, database, user
    )

    ds = _get_dataset(business_id, database)

    mapping = (
        ds.column_mapping
        if isinstance(ds.column_mapping, dict)
        else None
    )

    points = analytics_engine.sales_trend(
        ds.filepath, mapping
    )

    return schemas.TimeSeriesResponse(points=points)


@router.get(
    "/top-products/{business_id}",
    response_model=list[schemas.TopProduct]
)
def get_top_products(
    business_id: int,
    database: Session = Depends(db.get_db),
    user=Depends(get_current_user),
):
    get_accessible_business(
        business_id, database, user
    )

    ds = _get_dataset(business_id, database)

    mapping = (
        ds.column_mapping
        if isinstance(ds.column_mapping, dict)
        else None
    )

    return analytics_engine.top_products(
        ds.filepath,
        n=10,
        custom_mapping=mapping
    )


@router.get(
    "/category-performance/{business_id}",
    response_model=list[schemas.CategoryPerformance]
)
def get_category_performance(
    business_id: int,
    database: Session = Depends(db.get_db),
    user=Depends(get_current_user),
):
    get_accessible_business(
        business_id, database, user
    )

    ds = _get_dataset(business_id, database)

    mapping = (
        ds.column_mapping
        if isinstance(ds.column_mapping, dict)
        else None
    )

    return analytics_engine.category_performance(
        ds.filepath,
        custom_mapping=mapping
    )
