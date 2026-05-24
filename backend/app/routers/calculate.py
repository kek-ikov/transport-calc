from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import CalculateRequest, CalculateResponse
from app.services.calculator import calculate_transport_price


router = APIRouter(
    prefix="/calculate",
    tags=["Calculate"],
)


@router.post("", response_model=CalculateResponse)
def calculate_price(
    request: CalculateRequest,
    db: Session = Depends(get_db),
):
    return calculate_transport_price(
        db=db,
        from_city_id=request.from_city_id,
        to_city_id=request.to_city_id,
        cargo_length_mm=request.cargo_length_mm,
        cargo_width_mm=request.cargo_width_mm,
        cargo_height_mm=request.cargo_height_mm,
        cargo_weight_tons=request.cargo_weight_tons,
        escort_vehicle_count=request.escort_vehicle_count,
    )