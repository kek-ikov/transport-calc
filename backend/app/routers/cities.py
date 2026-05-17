from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import City, FederalSubject, Location
from app.schemas import CityResponse


router = APIRouter(
    prefix="/cities",
    tags=["Cities"],
)


@router.get("", response_model=list[CityResponse])
def search_cities(
    query: str = Query("", description="Поисковая строка, например: Москва"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = query.strip()

    statement = (
        select(City)
        .options(
            joinedload(City.subject).joinedload(FederalSubject.federal_district),
            joinedload(City.subject).joinedload(FederalSubject.tariff_zone),
        )
        .order_by(City.name)
        .limit(limit)
    )

    if query:
        search_pattern = f"%{query}%"

        statement = statement.where(
            or_(
                City.name.ilike(search_pattern),
                City.normalized_name.ilike(search_pattern),
            )
        )

    cities = db.execute(statement).scalars().all()

    result = []

    for city in cities:
        location = db.execute(
            select(Location).where(Location.city_id == city.id).limit(1)
        ).scalar_one_or_none()

        latitude = None
        longitude = None

        if location and location.latitude is not None and location.longitude is not None:
            latitude = float(location.latitude)
            longitude = float(location.longitude)
        elif city.latitude is not None and city.longitude is not None:
            latitude = float(city.latitude)
            longitude = float(city.longitude)

        result.append(
            CityResponse(
                id=city.id,
                name=city.name,
                normalized_name=city.normalized_name,
                subject_id=city.subject_id,
                subject_name=city.subject.name if city.subject else None,
                federal_district_name=(
                    city.subject.federal_district.name
                    if city.subject and city.subject.federal_district
                    else None
                ),
                tariff_zone_id=city.subject.tariff_zone_id if city.subject else None,
                tariff_zone_name=(
                    city.subject.tariff_zone.name
                    if city.subject and city.subject.tariff_zone
                    else None
                ),
                latitude=latitude,
                longitude=longitude,
                has_coordinates=latitude is not None and longitude is not None,
            )
        )

    return result