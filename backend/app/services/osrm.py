from decimal import Decimal, ROUND_HALF_UP

import httpx
from fastapi import HTTPException

from app.config import settings


def _to_decimal_km(distance_meters: float) -> Decimal:
    distance_km = Decimal(str(distance_meters)) / Decimal("1000")
    return distance_km.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)


def _to_minutes(duration_seconds: float) -> int:
    return int(round(duration_seconds / 60))


def _build_osrm_url(
    from_latitude,
    from_longitude,
    to_latitude,
    to_longitude,
) -> str:
    from_lat = float(from_latitude)
    from_lon = float(from_longitude)
    to_lat = float(to_latitude)
    to_lon = float(to_longitude)

    # Важно: OSRM принимает координаты в порядке longitude,latitude
    coordinates = f"{from_lon},{from_lat};{to_lon},{to_lat}"

    return f"{settings.OSRM_BASE_URL}/route/v1/driving/{coordinates}"


def _request_osrm(url: str, use_radiuses: bool = False) -> httpx.Response:
    params = {
        "overview": "false",
        "alternatives": "false",
        "steps": "false",
    }

    if use_radiuses:
        params["radiuses"] = "5000;5000"

    return httpx.get(
        url,
        params=params,
        timeout=30.0,
        trust_env=False,
    )


def get_distance_from_osrm(
    from_latitude,
    from_longitude,
    to_latitude,
    to_longitude,
) -> tuple[Decimal, int | None]:
    if from_latitude is None or from_longitude is None:
        raise HTTPException(
            status_code=400,
            detail="У точки отправления нет координат для OSRM",
        )

    if to_latitude is None or to_longitude is None:
        raise HTTPException(
            status_code=400,
            detail="У точки назначения нет координат для OSRM",
        )

    url = _build_osrm_url(
        from_latitude=from_latitude,
        from_longitude=from_longitude,
        to_latitude=to_latitude,
        to_longitude=to_longitude,
    )

    try:
        response = _request_osrm(url, use_radiuses=False)

        # Если обычный запрос не сработал, пробуем ещё раз,
        # разрешив OSRM искать ближайшую дорогу в радиусе 5 км.
        if response.status_code != 200:
            response = _request_osrm(url, use_radiuses=True)

    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail=(
                "Не удалось подключиться к OSRM. "
                "Проверь, что OSRM запущен на http://127.0.0.1:5000"
            ),
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="OSRM не ответил за 30 секунд",
        )
    except httpx.HTTPError as error:
        raise HTTPException(
            status_code=503,
            detail=f"Ошибка при обращении к OSRM: {error}",
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=503,
            detail={
                "message": f"OSRM вернул ошибку {response.status_code}",
                "url": str(response.url),
                "response_text": response.text,
            },
        )

    data = response.json()

    if data.get("code") != "Ok":
        raise HTTPException(
            status_code=400,
            detail={
                "message": "OSRM не смог построить маршрут",
                "url": str(response.url),
                "osrm_response": data,
            },
        )

    routes = data.get("routes", [])

    if not routes:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "OSRM не вернул ни одного маршрута",
                "url": str(response.url),
            },
        )

    route = routes[0]

    distance_meters = route.get("distance")
    duration_seconds = route.get("duration")

    if distance_meters is None:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "OSRM не вернул расстояние",
                "url": str(response.url),
                "osrm_response": data,
            },
        )

    distance_km = _to_decimal_km(distance_meters)
    duration_minutes = _to_minutes(duration_seconds) if duration_seconds is not None else None

    return distance_km, duration_minutes