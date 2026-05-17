from datetime import datetime
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import and_, select
from sqlalchemy.orm import Session, joinedload

from app.models import (
    Calculation,
    City,
    DistanceCache,
    FederalSubject,
    Location,
    Tariff,
    TariffDirection,
    TariffZone,
    TariffZoneSubject,
)
from app.services.osrm import get_distance_from_osrm


def get_city_or_404(db: Session, city_id: int) -> City:
    city = db.execute(
        select(City)
        .options(
            joinedload(City.subject).joinedload(FederalSubject.tariff_zone),
            joinedload(City.subject).joinedload(FederalSubject.federal_district),
        )
        .where(City.id == city_id)
    ).scalar_one_or_none()

    if city is None:
        raise HTTPException(
            status_code=404,
            detail=f"Город с id={city_id} не найден",
        )

    return city


def get_location_for_city_or_400(db: Session, city_id: int) -> Location:
    city = db.execute(
        select(City)
        .where(City.id == city_id)
    ).scalar_one_or_none()

    if city is None:
        raise HTTPException(
            status_code=404,
            detail=f"Город с id={city_id} не найден",
        )

    location = db.execute(
        select(Location)
        .where(Location.city_id == city_id)
        .limit(1)
    ).scalar_one_or_none()

    if location is not None:
        if location.latitude is not None and location.longitude is not None:
            return location

        if city.latitude is not None and city.longitude is not None:
            location.latitude = city.latitude
            location.longitude = city.longitude
            location.location_type = location.location_type or "city"
            location.name = location.name or city.name
            location.source = location.source or "synced_from_cities"

            db.commit()
            db.refresh(location)

            return location

        raise HTTPException(
            status_code=400,
            detail=(
                f"Для города {city.name} id={city_id} есть запись в locations, "
                "но нет координат ни в locations, ни в cities"
            ),
        )

    if city.latitude is None or city.longitude is None:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Для города {city.name} id={city_id} нет координат в cities "
                "и нет записи в locations"
            ),
        )

    location = Location(
        city_id=city.id,
        location_type="city",
        name=city.name,
        latitude=city.latitude,
        longitude=city.longitude,
        source="created_from_cities",
    )

    db.add(location)
    db.commit()
    db.refresh(location)

    return location


def get_federal_district_zone_name(federal_district_name: str) -> str | None:
    name = federal_district_name.lower()

    if "централь" in name:
        return "Центральный ФО"

    if "северо-запад" in name or "северо запад" in name:
        return "Северо-Западный ФО"

    if "южн" in name and "северо" not in name:
        return "Южный ФО"

    if "северо-кавказ" in name or "северо кавказ" in name:
        return "Северо-Кавказский ФО"

    if "приволж" in name:
        return "Приволжский ФО"

    if "ураль" in name:
        return "Уральский ФО"

    if "сибир" in name:
        return "Сибирский ФО"

    if "дальневост" in name:
        return "Дальний Восток"

    return None


def unique_tariff_zones(zones: list[TariffZone]) -> list[TariffZone]:
    result = []
    seen_ids = set()

    for zone in zones:
        if zone is None:
            continue

        if zone.id in seen_ids:
            continue

        seen_ids.add(zone.id)
        result.append(zone)

    return result


def get_subject_group_zones(db: Session, city: City) -> list[TariffZone]:
    zones = db.execute(
        select(TariffZone)
        .join(TariffZoneSubject, TariffZoneSubject.tariff_zone_id == TariffZone.id)
        .where(TariffZoneSubject.subject_id == city.subject_id)
        .order_by(TariffZone.id)
    ).scalars().all()

    return list(zones)


def get_district_tariff_zone(db: Session, city: City) -> TariffZone | None:
    if city.subject is None or city.subject.federal_district is None:
        return None

    zone_name = get_federal_district_zone_name(city.subject.federal_district.name)

    if zone_name is None:
        return None

    zone = db.execute(
        select(TariffZone)
        .where(TariffZone.name == zone_name)
        .limit(1)
    ).scalar_one_or_none()

    return zone


def get_tariff_zone_candidates(
    db: Session,
    city: City,
    role: str,
) -> list[TariffZone]:
    if city.subject is None:
        raise HTTPException(
            status_code=400,
            detail=f"Для города {city.name} не найден субъект РФ",
        )

    subject_group_zones = get_subject_group_zones(db, city)

    direct_zone = city.subject.tariff_zone

    district_zone = get_district_tariff_zone(db, city)

    if role == "destination":
        zones = [
            *subject_group_zones,
            direct_zone,
            district_zone,
        ]
    else:
        zones = [
            direct_zone,
            district_zone,
            *subject_group_zones,
        ]

    zones = unique_tariff_zones(zones)

    if not zones:
        raise HTTPException(
            status_code=400,
            detail=f"Для города {city.name} не удалось определить тарифную зону",
        )

    return zones


def find_city_to_zone_direction(
    db: Session,
    from_city_id: int,
    to_zone_candidates: list[TariffZone],
) -> tuple[TariffDirection, TariffZone] | None:
    for to_zone in to_zone_candidates:
        direction = db.execute(
            select(TariffDirection)
            .where(
                TariffDirection.from_city_id == from_city_id,
                TariffDirection.to_tariff_zone_id == to_zone.id,
                TariffDirection.direction_type == "city_to_zone",
            )
            .limit(1)
        ).scalar_one_or_none()

        if direction is not None:
            return direction, to_zone

    return None


def find_zone_to_zone_direction(
    db: Session,
    from_zone_candidates: list[TariffZone],
    to_zone_candidates: list[TariffZone],
) -> tuple[TariffDirection, TariffZone, TariffZone] | None:
    for from_zone in from_zone_candidates:
        for to_zone in to_zone_candidates:
            direction = db.execute(
                select(TariffDirection)
                .where(
                    TariffDirection.from_tariff_zone_id == from_zone.id,
                    TariffDirection.to_tariff_zone_id == to_zone.id,
                    TariffDirection.direction_type == "zone_to_zone",
                )
                .limit(1)
            ).scalar_one_or_none()

            if direction is not None:
                return direction, from_zone, to_zone

    return None


def find_direction_or_400(
    db: Session,
    from_city: City,
    to_city: City,
) -> tuple[TariffDirection, TariffZone | None, TariffZone]:
    from_zone_candidates = get_tariff_zone_candidates(
        db=db,
        city=from_city,
        role="origin",
    )

    to_zone_candidates = get_tariff_zone_candidates(
        db=db,
        city=to_city,
        role="destination",
    )

    city_to_zone_result = find_city_to_zone_direction(
        db=db,
        from_city_id=from_city.id,
        to_zone_candidates=to_zone_candidates,
    )

    if city_to_zone_result is not None:
        direction, to_zone = city_to_zone_result
        from_zone = from_zone_candidates[0] if from_zone_candidates else None
        return direction, from_zone, to_zone

    zone_to_zone_result = find_zone_to_zone_direction(
        db=db,
        from_zone_candidates=from_zone_candidates,
        to_zone_candidates=to_zone_candidates,
    )

    if zone_to_zone_result is not None:
        direction, from_zone, to_zone = zone_to_zone_result
        return direction, from_zone, to_zone

    from_zone_names = ", ".join(zone.name for zone in from_zone_candidates)
    to_zone_names = ", ".join(zone.name for zone in to_zone_candidates)

    raise HTTPException(
        status_code=400,
        detail=(
            "Не найдено тарифное направление. "
            f"Город отправления: {from_city.name}. "
            f"Возможные зоны отправления: {from_zone_names}. "
            f"Город назначения: {to_city.name}. "
            f"Возможные зоны назначения: {to_zone_names}."
        ),
    )


def find_tariff_or_400(
    db: Session,
    direction_id: int,
    cargo_length_mm: int,
    cargo_width_mm: int,
    cargo_height_mm: int,
    cargo_weight_tons: Decimal,
) -> Tariff:
    tariff = db.execute(
        select(Tariff)
        .where(
            Tariff.direction_id == direction_id,
            Tariff.max_length_mm >= cargo_length_mm,
            Tariff.max_width_mm >= cargo_width_mm,
            Tariff.max_height_mm >= cargo_height_mm,
            Tariff.max_weight_tons >= cargo_weight_tons,
        )
        .order_by(
            Tariff.max_length_mm,
            Tariff.max_width_mm,
            Tariff.max_height_mm,
            Tariff.max_weight_tons,
            Tariff.rate_per_km,
        )
        .limit(1)
    ).scalar_one_or_none()

    if tariff is None:
        raise HTTPException(
            status_code=400,
            detail=(
                "Не найден подходящий тариф для груза: "
                f"{cargo_length_mm}×{cargo_width_mm}×{cargo_height_mm} мм, "
                f"{cargo_weight_tons} т"
            ),
        )

    if tariff.rate_per_km is None:
        raise HTTPException(
            status_code=400,
            detail=f"У тарифа id={tariff.id} не заполнена ставка rate_per_km",
        )

    return tariff


def get_or_create_distance_cache(
    db: Session,
    from_location: Location,
    to_location: Location,
) -> DistanceCache:
    # 1. Сначала ищем уже готовое расстояние в кэше.
    # Не фильтруем по provider, потому что старые записи могли быть manual/test/imported.
    distance_cache = db.execute(
        select(DistanceCache)
        .where(
            and_(
                DistanceCache.from_location_id == from_location.id,
                DistanceCache.to_location_id == to_location.id,
            )
        )
        .limit(1)
    ).scalar_one_or_none()

    if distance_cache is not None:
        return distance_cache

    # 2. Если прямого маршрута нет, пробуем найти обратный.
    # Для расстояния обычно это допустимо: A → B примерно равно B → A.
    reverse_distance_cache = db.execute(
        select(DistanceCache)
        .where(
            and_(
                DistanceCache.from_location_id == to_location.id,
                DistanceCache.to_location_id == from_location.id,
            )
        )
        .limit(1)
    ).scalar_one_or_none()

    if reverse_distance_cache is not None:
        return reverse_distance_cache

    # 3. Если в кэше ничего нет — обращаемся к OSRM.
    distance_km, duration_minutes = get_distance_from_osrm(
        from_latitude=from_location.latitude,
        from_longitude=from_location.longitude,
        to_latitude=to_location.latitude,
        to_longitude=to_location.longitude,
    )

    # 4. Сохраняем новое расстояние в кэш.
    distance_cache = DistanceCache(
        from_location_id=from_location.id,
        to_location_id=to_location.id,
        provider="osrm",
        route_type="driving",
        distance_km=distance_km,
        duration_minutes=duration_minutes,
        calculated_at=datetime.utcnow(),
    )

    db.add(distance_cache)
    db.commit()
    db.refresh(distance_cache)

    return distance_cache


def calculate_transport_price(
    db: Session,
    from_city_id: int,
    to_city_id: int,
    cargo_length_mm: int,
    cargo_width_mm: int,
    cargo_height_mm: int,
    cargo_weight_tons: Decimal,
):
    from_city = get_city_or_404(db, from_city_id)
    to_city = get_city_or_404(db, to_city_id)

    from_location = get_location_for_city_or_400(db, from_city.id)
    to_location = get_location_for_city_or_400(db, to_city.id)

    direction, from_tariff_zone, to_tariff_zone = find_direction_or_400(
        db=db,
        from_city=from_city,
        to_city=to_city,
    )

    tariff = find_tariff_or_400(
        db=db,
        direction_id=direction.id,
        cargo_length_mm=cargo_length_mm,
        cargo_width_mm=cargo_width_mm,
        cargo_height_mm=cargo_height_mm,
        cargo_weight_tons=cargo_weight_tons,
    )

    distance_cache = get_or_create_distance_cache(
        db=db,
        from_location=from_location,
        to_location=to_location,
    )

    distance_km = Decimal(distance_cache.distance_km)
    rate_per_km = Decimal(tariff.rate_per_km)
    border_crossing_price = Decimal(tariff.border_crossing_price or 0)

    base_price = distance_km * rate_per_km
    final_price = base_price + border_crossing_price

    currency = tariff.currency or "RUB"

    explanation = (
        f"Маршрут: {from_city.name} → {to_city.name}. "
        f"Тарифное направление: {direction.name}. "
        f"Тариф: {tariff.cargo_type}, "
        f"до {tariff.max_length_mm}×{tariff.max_width_mm}×{tariff.max_height_mm} мм, "
        f"до {tariff.max_weight_tons} т. "
        f"Расстояние: {distance_km} км. "
        f"Расчёт: {distance_km} × {rate_per_km} + {border_crossing_price} = {final_price} {currency}."
    )

    calculation = Calculation(
        from_location_id=from_location.id,
        to_location_id=to_location.id,
        from_city_id=from_city.id,
        to_city_id=to_city.id,
        from_tariff_zone_id=from_tariff_zone.id if from_tariff_zone else None,
        to_tariff_zone_id=to_tariff_zone.id,
        direction_id=direction.id,
        tariff_id=tariff.id,
        distance_cache_id=distance_cache.id,
        cargo_length_mm=cargo_length_mm,
        cargo_width_mm=cargo_width_mm,
        cargo_height_mm=cargo_height_mm,
        cargo_weight_tons=cargo_weight_tons,
        cargo_type=tariff.cargo_type,
        distance_km=distance_km,
        rate_per_km=rate_per_km,
        base_price=base_price,
        border_crossing_price=border_crossing_price,
        final_price=final_price,
        currency=currency,
        explanation=explanation,
    )

    db.add(calculation)
    db.commit()
    db.refresh(calculation)

    return {
        "calculation_id": calculation.id,
        "from_city": from_city.name,
        "to_city": to_city.name,
        "from_location_id": from_location.id,
        "to_location_id": to_location.id,
        "from_tariff_zone_id": from_tariff_zone.id if from_tariff_zone else None,
        "from_tariff_zone_name": from_tariff_zone.name if from_tariff_zone else None,
        "to_tariff_zone_id": to_tariff_zone.id,
        "to_tariff_zone_name": to_tariff_zone.name,
        "direction_id": direction.id,
        "direction_name": direction.name,
        "tariff_id": tariff.id,
        "cargo_type": tariff.cargo_type,
        "distance_cache_id": distance_cache.id,
        "distance_km": distance_km,
        "rate_per_km": rate_per_km,
        "base_price": base_price,
        "border_crossing_price": border_crossing_price,
        "final_price": final_price,
        "currency": currency,
        "explanation": explanation,
    }