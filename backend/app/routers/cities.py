from fastapi import APIRouter, Depends, Query
from sqlalchemy import case, desc, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import City, FederalSubject
from app.schemas import CityResponse


router = APIRouter(
    prefix="/cities",
    tags=["Cities"],
)


def normalize_search_query(value: str) -> str:
    return (
        value.strip()
        .lower()
        .replace("ё", "е")
    )


@router.get("", response_model=list[CityResponse])
def search_cities(
    query: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    raw_query = query.strip()
    normalized_query = normalize_search_query(query)

    if not normalized_query:
        return []

    name_lower = func.lower(City.name)
    normalized_name_lower = func.lower(City.normalized_name)

    name_similarity = func.similarity(name_lower, normalized_query)
    normalized_similarity = func.similarity(normalized_name_lower, normalized_query)

    best_similarity = func.greatest(
        name_similarity,
        normalized_similarity,
    )

    priority = case(
        (
            or_(
                name_lower == normalized_query,
                normalized_name_lower == normalized_query,
            ),
            1,
        ),

        (
            or_(
                name_lower.like(f"{normalized_query}%"),
                normalized_name_lower.like(f"{normalized_query}%"),
            ),
            2,
        ),

        (
            or_(
                name_lower.like(f"%{normalized_query}%"),
                normalized_name_lower.like(f"%{normalized_query}%"),
            ),
            3,
        ),

        else_=4,
    )

    cities = db.execute(
        select(City)
        .options(
            joinedload(City.subject).joinedload(FederalSubject.tariff_zone),
        )
        .where(
            or_(
                name_lower.like(f"%{normalized_query}%"),
                normalized_name_lower.like(f"%{normalized_query}%"),
                name_similarity >= 0.25,
                normalized_similarity >= 0.25,
            )
        )
        .order_by(
            priority.asc(),
            desc(best_similarity),
            City.name.asc(),
        )
        .limit(limit)
    ).scalars().all()

    return [
        CityResponse(
            id=city.id,
            name=city.name,
            normalized_name=city.normalized_name,

            subject_id=city.subject_id,
            subject_name=city.subject.name if city.subject else None,

            tariff_zone_id=(
                city.subject.tariff_zone_id
                if city.subject
                else None
            ),
            tariff_zone_name=(
                city.subject.tariff_zone.name
                if city.subject and city.subject.tariff_zone
                else None
            ),

            latitude=float(city.latitude) if city.latitude is not None else None,
            longitude=float(city.longitude) if city.longitude is not None else None,
            has_coordinates=True,
        )
        for city in cities
    ]