from fastapi import APIRouter

from app.services.osrm import get_distance_from_osrm


router = APIRouter(
    prefix="/osrm",
    tags=["OSRM"],
)


@router.get("/test")
def test_osrm():
    distance_km, duration_minutes = get_distance_from_osrm(
        from_latitude=55.7558,
        from_longitude=37.6173,
        to_latitude=52.2864036,
        to_longitude=104.2807466,
    )

    return {
        "from": "Москва",
        "to": "Иркутск",
        "distance_km": distance_km,
        "duration_minutes": duration_minutes,
    }