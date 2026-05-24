from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException
from sqlalchemy import and_, select
from sqlalchemy.orm import Session, joinedload

from app.models import (
    AdditionalService,
    Calculation,
    CargoSizeCategory,
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


def money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def distance_value(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def get_city_or_404(db: Session, city_id: int) -> City:
    city = db.execute(
        select(City)
        .options(
            joinedload(City.subject).joinedload(FederalSubject.tariff_zone),
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


def unique_tariff_zones(zones: list[TariffZone | None]) -> list[TariffZone]:
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

    if role == "destination":
        zones = [
            *subject_group_zones,
            direct_zone,
        ]
    else:
        zones = [
            direct_zone,
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


def get_or_create_distance_cache(
    db: Session,
    from_location: Location,
    to_location: Location,
) -> DistanceCache:
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

    distance_km, duration_minutes = get_distance_from_osrm(
        from_latitude=from_location.latitude,
        from_longitude=from_location.longitude,
        to_latitude=to_location.latitude,
        to_longitude=to_location.longitude,
    )

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


def find_cargo_size_category_or_400(
    db: Session,
    cargo_length_mm: int,
    cargo_width_mm: int,
    cargo_height_mm: int,
) -> CargoSizeCategory:
    category = db.execute(
        select(CargoSizeCategory)
        .where(
            CargoSizeCategory.max_length_mm >= cargo_length_mm,
            CargoSizeCategory.max_width_mm >= cargo_width_mm,
            CargoSizeCategory.max_height_mm >= cargo_height_mm,
        )
        .order_by(CargoSizeCategory.priority)
        .limit(1)
    ).scalar_one_or_none()

    if category is None:
        raise HTTPException(
            status_code=400,
            detail=(
                "Груз превышает максимальные допустимые габариты: "
                f"{cargo_length_mm}×{cargo_width_mm}×{cargo_height_mm} мм. "
                "Максимум по текущей таблице: 40000×5000×5000 мм."
            ),
        )

    return category


def get_base_tariff_category_ids(
    cargo_size_category: CargoSizeCategory,
    cargo_weight_tons: Decimal,
) -> list[int]:
    """
    В таблице tariffs обычно:
    1 = Габарит 20 т
    2 = Негабаритные/тяжёлые строки
    3 = Негабарит 2 степени, но это категория надбавки +80 руб/км.

    Поэтому:
    - для габарита до 20 т сначала ищем категорию 1, потом fallback на 2;
    - для габарита тяжелее 20 т ищем категорию 2;
    - для негабарита 1 ищем категорию 2;
    - для негабарита 2 ищем категорию 2, а +80 берём из категории 3.
    """
    if cargo_size_category.code == "standard" and cargo_weight_tons <= Decimal("20"):
        return [1, 2]

    return [2]


def find_tariff_or_400(
    db: Session,
    direction_id: int,
    cargo_size_category: CargoSizeCategory,
    cargo_weight_tons: Decimal,
    distance_km: Decimal,
) -> Tariff:
    base_category_ids = get_base_tariff_category_ids(
        cargo_size_category=cargo_size_category,
        cargo_weight_tons=cargo_weight_tons,
    )

    for base_category_id in base_category_ids:
        tariff = db.execute(
            select(Tariff)
            .where(
                Tariff.direction_id == direction_id,
                Tariff.cargo_size_category_id == base_category_id,
                cargo_weight_tons > Tariff.min_weight_tons,
                cargo_weight_tons <= Tariff.max_weight_tons,
                distance_km > Tariff.min_distance_km,
                (
                    Tariff.max_distance_km.is_(None)
                    | (distance_km <= Tariff.max_distance_km)
                ),
            )
            .order_by(
                Tariff.max_weight_tons,
                Tariff.min_distance_km,
                Tariff.rate_per_km,
            )
            .limit(1)
        ).scalar_one_or_none()

        if tariff is not None:
            return tariff

    raise HTTPException(
        status_code=400,
        detail=(
            "Не найден подходящий тариф. "
            f"direction_id={direction_id}, "
            f"габаритная категория={cargo_size_category.name}, "
            f"вес={cargo_weight_tons} т, "
            f"расстояние={distance_km} км."
        ),
    )


def get_escort_vehicle_rate_per_km(db: Session) -> Decimal:
    service = db.execute(
        select(AdditionalService)
        .where(
            AdditionalService.code == "escort_vehicle",
            AdditionalService.is_active.is_(True),
        )
        .limit(1)
    ).scalar_one_or_none()

    if service is None:
        return Decimal("0.00")

    return Decimal(service.price or 0)


def calculate_transport_price(
    db: Session,
    from_city_id: int,
    to_city_id: int,
    cargo_length_mm: int,
    cargo_width_mm: int,
    cargo_height_mm: int,
    cargo_weight_tons: Decimal,
    escort_vehicle_count: int = 0,
):
    if escort_vehicle_count < 0:
        raise HTTPException(
            status_code=400,
            detail="Количество автомобилей прикрытия не может быть меньше 0",
        )

    from_city = get_city_or_404(db, from_city_id)
    to_city = get_city_or_404(db, to_city_id)

    from_location = get_location_for_city_or_400(db, from_city.id)
    to_location = get_location_for_city_or_400(db, to_city.id)

    direction, from_tariff_zone, to_tariff_zone = find_direction_or_400(
        db=db,
        from_city=from_city,
        to_city=to_city,
    )

    distance_cache = get_or_create_distance_cache(
        db=db,
        from_location=from_location,
        to_location=to_location,
    )

    distance_km = distance_value(Decimal(distance_cache.distance_km))

    cargo_size_category = find_cargo_size_category_or_400(
        db=db,
        cargo_length_mm=cargo_length_mm,
        cargo_width_mm=cargo_width_mm,
        cargo_height_mm=cargo_height_mm,
    )

    tariff = find_tariff_or_400(
        db=db,
        direction_id=direction.id,
        cargo_size_category=cargo_size_category,
        cargo_weight_tons=Decimal(cargo_weight_tons),
        distance_km=distance_km,
    )

    base_rate_per_km = Decimal(tariff.rate_per_km)
    cargo_size_surcharge_per_km = Decimal(cargo_size_category.rate_per_km_surcharge)

    escort_vehicle_rate_per_km = get_escort_vehicle_rate_per_km(db)

    final_rate_per_km = money(base_rate_per_km + cargo_size_surcharge_per_km)

    base_price = money(distance_km * base_rate_per_km)
    cargo_size_surcharge_price = money(distance_km * cargo_size_surcharge_per_km)

    additional_services_price = money(
        distance_km
        * escort_vehicle_rate_per_km
        * Decimal(escort_vehicle_count)
    )

    special_tariffs_price = Decimal("0.00")

    final_price = money(
        base_price
        + cargo_size_surcharge_price
        + additional_services_price
        + special_tariffs_price
    )

    currency = tariff.currency or "RUB"

    explanation = (
        f"Маршрут: {from_city.name} → {to_city.name}. "
        f"Тарифное направление: {direction.name}. "
        f"Габаритная категория: {cargo_size_category.name}. "
        f"Груз: {cargo_length_mm}×{cargo_width_mm}×{cargo_height_mm} мм, "
        f"{cargo_weight_tons} т. "
        f"Расстояние: {distance_km} км. "
        f"Базовая ставка: {base_rate_per_km} {currency}/км. "
        f"Надбавка за габарит: {cargo_size_surcharge_per_km} {currency}/км. "
        f"Итоговая ставка без прикрытия: {final_rate_per_km} {currency}/км. "
        f"Автомобили прикрытия: {escort_vehicle_count} × "
        f"{escort_vehicle_rate_per_km} {currency}/км. "
        f"Расчёт: {base_price} + {cargo_size_surcharge_price} "
        f"+ {additional_services_price} = {final_price} {currency}."
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
        cargo_size_category_id=cargo_size_category.id,
        distance_cache_id=distance_cache.id,

        cargo_length_mm=cargo_length_mm,
        cargo_width_mm=cargo_width_mm,
        cargo_height_mm=cargo_height_mm,
        cargo_weight_tons=cargo_weight_tons,

        distance_km=distance_km,

        base_rate_per_km=base_rate_per_km,
        cargo_size_surcharge_per_km=cargo_size_surcharge_per_km,

        escort_vehicle_count=escort_vehicle_count,
        escort_vehicle_rate_per_km=escort_vehicle_rate_per_km,

        final_rate_per_km=final_rate_per_km,

        base_price=base_price,
        cargo_size_surcharge_price=cargo_size_surcharge_price,
        additional_services_price=additional_services_price,
        special_tariffs_price=special_tariffs_price,
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

        "cargo_size_category_id": cargo_size_category.id,
        "cargo_size_category_name": cargo_size_category.name,

        "distance_cache_id": distance_cache.id,
        "distance_km": distance_km,

        "base_rate_per_km": base_rate_per_km,
        "cargo_size_surcharge_per_km": cargo_size_surcharge_per_km,
        "escort_vehicle_rate_per_km": escort_vehicle_rate_per_km,
        "escort_vehicle_count": escort_vehicle_count,
        "final_rate_per_km": final_rate_per_km,

        "base_price": base_price,
        "cargo_size_surcharge_price": cargo_size_surcharge_price,
        "additional_services_price": additional_services_price,
        "special_tariffs_price": special_tariffs_price,
        "final_price": final_price,

        "currency": currency,
        "explanation": explanation,
    }