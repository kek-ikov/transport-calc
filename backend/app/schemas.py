from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CityResponse(BaseModel):
    id: int
    name: str
    normalized_name: str

    subject_id: int
    subject_name: str | None = None

    tariff_zone_id: int | None = None
    tariff_zone_name: str | None = None

    latitude: float | None = None
    longitude: float | None = None
    has_coordinates: bool

    model_config = ConfigDict(from_attributes=True)


class CalculateRequest(BaseModel):
    from_city_id: int = Field(..., examples=[1490])
    to_city_id: int = Field(..., examples=[365])

    cargo_length_mm: int = Field(..., gt=0, examples=[15000])
    cargo_width_mm: int = Field(..., gt=0, examples=[3490])
    cargo_height_mm: int = Field(..., gt=0, examples=[3500])
    cargo_weight_tons: Decimal = Field(..., gt=0, examples=[25])

    escort_vehicle_count: int = Field(
        default=0,
        ge=0,
        le=10,
        examples=[1],
        description="Количество автомобилей прикрытия. 0 — не требуется.",
    )


class CalculateResponse(BaseModel):
    calculation_id: int

    from_city: str
    to_city: str

    from_location_id: int
    to_location_id: int

    from_tariff_zone_id: int | None = None
    from_tariff_zone_name: str | None = None

    to_tariff_zone_id: int
    to_tariff_zone_name: str

    direction_id: int
    direction_name: str

    tariff_id: int

    cargo_size_category_id: int
    cargo_size_category_name: str

    distance_cache_id: int
    distance_km: Decimal

    base_rate_per_km: Decimal
    cargo_size_surcharge_per_km: Decimal
    escort_vehicle_rate_per_km: Decimal
    escort_vehicle_count: int
    final_rate_per_km: Decimal

    base_price: Decimal
    cargo_size_surcharge_price: Decimal
    additional_services_price: Decimal
    special_tariffs_price: Decimal
    final_price: Decimal

    currency: str
    explanation: str


class LocationResponse(BaseModel):
    id: int
    city_id: int | None = None
    city_name: str | None = None
    location_type: str
    name: str | None = None
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    source: str | None = None

    model_config = ConfigDict(from_attributes=True)


class CityLocationUpsertRequest(BaseModel):
    city_id: int = Field(..., examples=[365])
    latitude: Decimal = Field(..., examples=[55.7558])
    longitude: Decimal = Field(..., examples=[37.6173])
    source: str = Field(default="manual", examples=["manual"])


class CalculationHistoryItem(BaseModel):
    id: int

    from_city_id: int | None = None
    from_city_name: str | None = None

    to_city_id: int | None = None
    to_city_name: str | None = None

    direction_id: int | None = None
    direction_name: str | None = None

    tariff_id: int | None = None

    cargo_size_category_id: int | None = None
    cargo_size_category_name: str | None = None

    cargo_length_mm: int
    cargo_width_mm: int
    cargo_height_mm: int
    cargo_weight_tons: Decimal

    distance_km: Decimal | None = None

    base_rate_per_km: Decimal | None = None
    cargo_size_surcharge_per_km: Decimal | None = None
    escort_vehicle_count: int | None = None
    escort_vehicle_rate_per_km: Decimal | None = None
    final_rate_per_km: Decimal | None = None

    base_price: Decimal | None = None
    cargo_size_surcharge_price: Decimal | None = None
    additional_services_price: Decimal | None = None
    special_tariffs_price: Decimal | None = None
    final_price: Decimal | None = None

    currency: str | None = None
    explanation: str | None = None
    created_at: datetime | None = None