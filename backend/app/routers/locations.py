from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import City, Location
from app.schemas import CityLocationUpsertRequest, LocationResponse


router = APIRouter(
    prefix="/locations",
    tags=["Locations"],
)


@router.get("/available", response_model=list[LocationResponse])
def get_available_locations(
    db: Session = Depends(get_db),
):
    locations = db.execute(
        select(Location)
        .options(joinedload(Location.city))
        .where(
            Location.city_id.is_not(None),
            Location.latitude.is_not(None),
            Location.longitude.is_not(None),
        )
        .order_by(Location.id)
    ).scalars().all()

    result = []

    for location in locations:
        result.append(
            LocationResponse(
                id=location.id,
                city_id=location.city_id,
                city_name=location.city.name if location.city else None,
                location_type=location.location_type,
                name=location.name,
                latitude=location.latitude,
                longitude=location.longitude,
                source=location.source,
            )
        )

    return result


@router.post("/city", response_model=LocationResponse)
def upsert_city_location(
    request: CityLocationUpsertRequest,
    db: Session = Depends(get_db),
):
    city = db.execute(
        select(City).where(City.id == request.city_id)
    ).scalar_one_or_none()

    if city is None:
        raise HTTPException(
            status_code=404,
            detail=f"Город с id={request.city_id} не найден",
        )

    location = db.execute(
        select(Location)
        .where(Location.city_id == request.city_id)
        .limit(1)
    ).scalar_one_or_none()

    if location is None:
        location = Location(
            city_id=city.id,
            location_type="city",
            name=city.name,
            latitude=request.latitude,
            longitude=request.longitude,
            source=request.source,
        )
        db.add(location)
    else:
        location.location_type = location.location_type or "city"
        location.name = location.name or city.name
        location.latitude = request.latitude
        location.longitude = request.longitude
        location.source = request.source

    city.latitude = request.latitude
    city.longitude = request.longitude

    db.commit()
    db.refresh(location)

    return LocationResponse(
        id=location.id,
        city_id=location.city_id,
        city_name=city.name,
        location_type=location.location_type,
        name=location.name,
        latitude=location.latitude,
        longitude=location.longitude,
        source=location.source,
    )