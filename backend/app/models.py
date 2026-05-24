from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TariffZone(Base):
    __tablename__ = "tariff_zones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    zone_type: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)


class TariffZoneSubject(Base):
    __tablename__ = "tariff_zone_subjects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    tariff_zone_id: Mapped[int] = mapped_column(
        ForeignKey("tariff_zones.id"),
        nullable=False,
    )

    subject_id: Mapped[int] = mapped_column(
        ForeignKey("federal_subjects.id"),
        nullable=False,
    )

    tariff_zone: Mapped[TariffZone] = relationship()


class FederalSubject(Base):
    __tablename__ = "federal_subjects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    tariff_zone_id: Mapped[int | None] = mapped_column(
        ForeignKey("tariff_zones.id"),
    )

    name: Mapped[str] = mapped_column(Text, nullable=False)
    subject_type: Mapped[str | None] = mapped_column(Text)

    tariff_zone: Mapped[TariffZone | None] = relationship()


class City(Base):
    __tablename__ = "cities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    subject_id: Mapped[int] = mapped_column(
        ForeignKey("federal_subjects.id"),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_name: Mapped[str] = mapped_column(Text, nullable=False)

    latitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7))
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7))

    subject: Mapped[FederalSubject] = relationship()


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    city_id: Mapped[int | None] = mapped_column(
        ForeignKey("cities.id"),
    )

    location_type: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str | None] = mapped_column(Text)
    address: Mapped[str | None] = mapped_column(Text)

    latitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7))
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7))

    geocoder_provider: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(Text)

    city: Mapped[City | None] = relationship()


class TariffDirection(Base):
    __tablename__ = "tariff_directions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    name: Mapped[str] = mapped_column(Text, nullable=False)

    from_city_id: Mapped[int | None] = mapped_column(
        ForeignKey("cities.id"),
    )

    from_tariff_zone_id: Mapped[int | None] = mapped_column(
        ForeignKey("tariff_zones.id"),
    )

    to_tariff_zone_id: Mapped[int | None] = mapped_column(
        ForeignKey("tariff_zones.id"),
    )

    direction_type: Mapped[str] = mapped_column(Text, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text)

    from_city: Mapped[City | None] = relationship(
        foreign_keys=[from_city_id],
    )

    from_tariff_zone: Mapped[TariffZone | None] = relationship(
        foreign_keys=[from_tariff_zone_id],
    )

    to_tariff_zone: Mapped[TariffZone | None] = relationship(
        foreign_keys=[to_tariff_zone_id],
    )


class CargoSizeCategory(Base):
    __tablename__ = "cargo_size_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    code: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)

    max_length_mm: Mapped[int] = mapped_column(Integer, nullable=False)
    max_width_mm: Mapped[int] = mapped_column(Integer, nullable=False)
    max_height_mm: Mapped[int] = mapped_column(Integer, nullable=False)

    rate_per_km_surcharge: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    priority: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text)


class Tariff(Base):
    __tablename__ = "tariffs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    direction_id: Mapped[int] = mapped_column(
        ForeignKey("tariff_directions.id"),
        nullable=False,
    )

    cargo_size_category_id: Mapped[int] = mapped_column(
        ForeignKey("cargo_size_categories.id"),
        nullable=False,
    )

    min_weight_tons: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    max_weight_tons: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    min_distance_km: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    max_distance_km: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))

    rate_per_km: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    currency: Mapped[str] = mapped_column(Text, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text)

    direction: Mapped[TariffDirection] = relationship()
    cargo_size_category: Mapped[CargoSizeCategory] = relationship()


class AdditionalService(Base):
    __tablename__ = "additional_services"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    code: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)

    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    price_unit: Mapped[str] = mapped_column(Text, nullable=False)
    currency: Mapped[str] = mapped_column(Text, nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text)


class SpecialTariff(Base):
    __tablename__ = "special_tariffs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    name: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(Text, nullable=False)

    cargo_size_category_id: Mapped[int | None] = mapped_column(
        ForeignKey("cargo_size_categories.id"),
    )

    min_weight_tons: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    max_weight_tons: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))

    min_distance_km: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    max_distance_km: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))

    price: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    price_unit: Mapped[str] = mapped_column(Text, nullable=False)
    currency: Mapped[str] = mapped_column(Text, nullable=False)

    raw_value: Mapped[str | None] = mapped_column(Text)
    comment: Mapped[str | None] = mapped_column(Text)

    cargo_size_category: Mapped[CargoSizeCategory | None] = relationship()


class DistanceCache(Base):
    __tablename__ = "distance_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    from_location_id: Mapped[int] = mapped_column(
        ForeignKey("locations.id"),
        nullable=False,
    )

    to_location_id: Mapped[int] = mapped_column(
        ForeignKey("locations.id"),
        nullable=False,
    )

    provider: Mapped[str] = mapped_column(Text, nullable=False)
    route_type: Mapped[str] = mapped_column(Text, nullable=False)

    distance_km: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    duration_minutes: Mapped[int | None] = mapped_column(Integer)

    calculated_at: Mapped[datetime | None] = mapped_column(DateTime)

    from_location: Mapped[Location] = relationship(
        foreign_keys=[from_location_id],
    )

    to_location: Mapped[Location] = relationship(
        foreign_keys=[to_location_id],
    )


class Calculation(Base):
    __tablename__ = "calculations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    from_location_id: Mapped[int | None] = mapped_column(ForeignKey("locations.id"))
    to_location_id: Mapped[int | None] = mapped_column(ForeignKey("locations.id"))

    from_city_id: Mapped[int | None] = mapped_column(ForeignKey("cities.id"))
    to_city_id: Mapped[int | None] = mapped_column(ForeignKey("cities.id"))

    from_tariff_zone_id: Mapped[int | None] = mapped_column(
        ForeignKey("tariff_zones.id")
    )
    to_tariff_zone_id: Mapped[int | None] = mapped_column(
        ForeignKey("tariff_zones.id")
    )

    direction_id: Mapped[int | None] = mapped_column(
        ForeignKey("tariff_directions.id")
    )

    tariff_id: Mapped[int | None] = mapped_column(
        ForeignKey("tariffs.id")
    )

    cargo_size_category_id: Mapped[int | None] = mapped_column(
        ForeignKey("cargo_size_categories.id")
    )

    distance_cache_id: Mapped[int | None] = mapped_column(
        ForeignKey("distance_cache.id")
    )

    cargo_length_mm: Mapped[int] = mapped_column(Integer, nullable=False)
    cargo_width_mm: Mapped[int] = mapped_column(Integer, nullable=False)
    cargo_height_mm: Mapped[int] = mapped_column(Integer, nullable=False)
    cargo_weight_tons: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    distance_km: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    base_rate_per_km: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    cargo_size_surcharge_per_km: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    escort_vehicle_count: Mapped[int] = mapped_column(Integer, nullable=False)
    escort_vehicle_rate_per_km: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    final_rate_per_km: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    base_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    cargo_size_surcharge_price: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )
    additional_services_price: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )
    special_tariffs_price: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )
    final_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)

    currency: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

    from_city: Mapped[City | None] = relationship(
        foreign_keys=[from_city_id],
    )

    to_city: Mapped[City | None] = relationship(
        foreign_keys=[to_city_id],
    )

    direction: Mapped[TariffDirection | None] = relationship()
    tariff: Mapped[Tariff | None] = relationship()
    cargo_size_category: Mapped[CargoSizeCategory | None] = relationship()
    distance_cache: Mapped[DistanceCache | None] = relationship()