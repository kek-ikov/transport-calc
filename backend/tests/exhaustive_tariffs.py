"""Run only against a disposable database: full calculations create history rows."""
import json
import os
from pathlib import Path
from decimal import Decimal as D
from types import SimpleNamespace as Obj
from unittest.mock import patch
from sqlalchemy import select
from fastapi import HTTPException
from app.database import SessionLocal
from app.models import Tariff,CargoSizeCategory,City
from app.services import calculator as c

db=SessionLocal(); count=0
cats={x.id:x for x in db.scalars(select(CargoSizeCategory))}
rates=list(db.scalars(select(Tariff)))
for t in rates:
    for w in [t.min_weight_tons+D('.01'),t.max_weight_tons]:
        got=c.find_tariff_or_400(db,t.direction_id,cats[t.cargo_size_category_id],w,D('1000'))
        assert got.id==t.id,(t.id,w,got.id)
        count+=1
# Every heavy band must also be usable by dimensionally standard cargo.
for t in rates:
    if t.cargo_size_category_id==2 and t.max_weight_tons>20:
        got=c.find_tariff_or_400(db,t.direction_id,cats[1],t.max_weight_tons,D('1000'))
        assert got.id==t.id
        count+=1
raw=json.loads(Path(os.environ.get('TARIFF_SOURCE', str(Path(__file__).resolve().parents[2] / 'migrations/sources/regional-20261117-corrected.json'))).read_text())
def expected(dist,dims,w):
    candidates=[r for r in raw if r['min_km']<dist<=r['max_km'] and all(a<=r[k] for a,k in zip(dims,['length','width','height'])) and w<=r['weight']]
    if not candidates:return None
    candidates.sort(key=lambda r:(r['length']*r['width']*r['height'],r['weight']))
    r=candidates[0]
    equal=[x for x in candidates if (x['length'],x['width'],x['height'],x['weight'])==(r['length'],r['width'],r['height'],r['weight'])]
    prices={x['price'] for x in equal}
    return next(iter(prices)) if len(prices)==1 else None
mos=db.scalar(select(City).where(City.name=='Москва'));pod=db.scalar(select(City).where(City.name=='Подольск'))
for dist in [D(x) for x in ['0.001','50','50.001','100','100.001','150','150.001','200','200.001','300','300.001','400','400.001','500','500.001','600']]:
    for dims in [(12000,2500,3100),(15000,3490,3500),(18000,4200,3800),(18001,4200,3800)]:
        for w in [D(x) for x in ['20','20.01','25','25.01','55','55.01','60','60.01']]:
            price=expected(dist,dims,w)
            with patch.object(c,'get_or_create_distance_cache',return_value=Obj(id=1,distance_km=dist)):
                try:r=c.calculate_transport_price(db,mos.id,pod.id,*dims,w)
                except HTTPException as e:
                    assert price is None,(dist,dims,w,price,e.detail)
                else:assert price is not None and r['final_price']==D(str(price)),(dist,dims,w,price,r['final_price'])
            count+=1
for dims,cat in [((13000,2550,3100),1),((13001,2550,3100),2),((17000,3490,3850),2),((17001,3490,3850),3),((40000,5000,5000),3)]:
    assert c.find_cargo_size_category_or_400(db,*dims).id==cat;count+=1
try:c.find_cargo_size_category_or_400(db,40001,5000,5000);raise AssertionError('oversize accepted')
except HTTPException:count+=1
print('PASS',count,'boundary cases')
