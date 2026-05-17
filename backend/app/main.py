from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.database import check_database_connection
from app.routers import calculate, calculations, cities, locations, osrm


app = FastAPI(
    title="Transport Calculator API",
    description="API для расчёта стоимости перевозки",
    version="0.1.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(cities.router)
app.include_router(locations.router)
app.include_router(calculate.router)
app.include_router(osrm.router)
app.include_router(calculations.router)


@app.get("/health")
def health_check():
    db_is_connected = check_database_connection()

    return {
        "status": "ok" if db_is_connected else "error",
        "database": "connected" if db_is_connected else "not connected"
    }

frontend_dist_path = Path(__file__).resolve().parents[2] / "frontend" / "dist"
frontend_assets_path = frontend_dist_path / "assets"


if frontend_assets_path.exists():
    app.mount(
        "/assets",
        StaticFiles(directory=frontend_assets_path),
        name="frontend-assets",
    )


@app.get("/favicon.svg", include_in_schema=False)
def favicon():
    favicon_path = frontend_dist_path / "favicon.svg"

    if favicon_path.exists():
        return FileResponse(
            favicon_path,
            media_type="image/svg+xml",
            headers={"Cache-Control": "no-cache"},
        )

    return FileResponse(
        frontend_dist_path / "index.html",
        media_type="text/html",
        headers={"Cache-Control": "no-cache"},
    )


@app.get("/", include_in_schema=False)
def serve_frontend_root():
    return FileResponse(
        frontend_dist_path / "index.html",
        media_type="text/html",
        headers={"Cache-Control": "no-cache"},
    )


@app.get("/{full_path:path}", include_in_schema=False)
def serve_frontend(full_path: str):
    return FileResponse(
        frontend_dist_path / "index.html",
        media_type="text/html",
        headers={"Cache-Control": "no-cache"},
    )