from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, select
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Calculation
from app.schemas import CalculationHistoryItem


router = APIRouter(
    prefix="/calculations",
    tags=["Calculations"],
)


@router.get("/recent", response_model=list[CalculationHistoryItem])
def get_recent_calculations(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    calculations = db.execute(
        select(Calculation)
        .options(
            joinedload(Calculation.from_city),
            joinedload(Calculation.to_city),
            joinedload(Calculation.direction),
            joinedload(Calculation.tariff),
            joinedload(Calculation.cargo_size_category),
        )
        .order_by(desc(Calculation.created_at), desc(Calculation.id))
        .limit(limit)
    ).scalars().all()

    result = []

    for calculation in calculations:
        result.append(
            CalculationHistoryItem(
                id=calculation.id,

                from_city_id=calculation.from_city_id,
                from_city_name=calculation.from_city.name if calculation.from_city else None,

                to_city_id=calculation.to_city_id,
                to_city_name=calculation.to_city.name if calculation.to_city else None,

                direction_id=calculation.direction_id,
                direction_name=calculation.direction.name if calculation.direction else None,

                tariff_id=calculation.tariff_id,

                cargo_size_category_id=calculation.cargo_size_category_id,
                cargo_size_category_name=(
                    calculation.cargo_size_category.name
                    if calculation.cargo_size_category
                    else None
                ),

                cargo_length_mm=calculation.cargo_length_mm,
                cargo_width_mm=calculation.cargo_width_mm,
                cargo_height_mm=calculation.cargo_height_mm,
                cargo_weight_tons=calculation.cargo_weight_tons,

                distance_km=calculation.distance_km,

                base_rate_per_km=calculation.base_rate_per_km,
                cargo_size_surcharge_per_km=calculation.cargo_size_surcharge_per_km,
                escort_vehicle_count=calculation.escort_vehicle_count,
                escort_vehicle_rate_per_km=calculation.escort_vehicle_rate_per_km,
                final_rate_per_km=calculation.final_rate_per_km,

                base_price=calculation.base_price,
                cargo_size_surcharge_price=calculation.cargo_size_surcharge_price,
                additional_services_price=calculation.additional_services_price,
                special_tariffs_price=calculation.special_tariffs_price,
                final_price=calculation.final_price,

                currency=calculation.currency,
                explanation=calculation.explanation,
                created_at=calculation.created_at,
            )
        )

    return result