from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch
from sqlalchemy import select, text
from fastapi import HTTPException
from app.database import SessionLocal
from app.models import City, CargoSizeCategory, FixedDistanceTariff
from app.services import calculator as c

db=SessionLocal()
def city(n): return db.scalar(select(City).where(City.name==n))
def calc(a,b,d,w=20,dims=(12000,2500,3100)):
    with patch.object(c, "get_or_create_distance_cache", return_value=SimpleNamespace(id=1,distance_km=Decimal(str(d)))):
        return c.calculate_transport_price(db,city(a).id,city(b).id,*dims,Decimal(str(w)))
for d,price in [(50,40000),(50.001,55000),(100,55000),(100.001,60000),(500,105000)]:
    assert calc("Москва","Подольск",d)["final_price"]==price
for d in [500.001,600]:
    try: calc("Москва","Подольск",d); raise AssertionError("missing quote")
    except HTTPException as e: assert "не заполнена" in e.detail
assert calc("Хабаровск","Подольск",1000,25)["base_rate_per_km"]>0
r=calc("Мурманск","Петрозаводск",400)
assert r["calculation_type"]=="per_km"
assert db.scalar(select(FixedDistanceTariff.id).where(FixedDistanceTariff.source_version=="regional-20261117-corrected"))
# Detect overlapping weight/distance bands independently of the selector.
q="""SELECT count(*) FROM tariffs a JOIN tariffs b ON a.id<b.id AND a.direction_id=b.direction_id AND a.cargo_size_category_id=b.cargo_size_category_id AND a.min_weight_tons<b.max_weight_tons AND b.min_weight_tons<a.max_weight_tons AND a.min_distance_km<=coalesce(b.max_distance_km,1e9) AND b.min_distance_km<=coalesce(a.max_distance_km,1e9)"""
assert db.scalar(text(q))==0
print("PASS: boundaries, missing prices, heavy standard cargo, cross-region route, tariff overlaps")
