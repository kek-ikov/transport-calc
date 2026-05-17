# Transport Calculator

Прототип калькулятора стоимости перевозки.

Проект рассчитывает стоимость маршрута на основе:

- города отправления
- города назначения
- габаритов груза
- веса груза
- тарифных зон
- тарифных направлений
- дорожного расстояния, рассчитанного через OSRM

---

## Что входит в проект

```text
transport-calc/
  backend/       FastAPI backend
  frontend/      React frontend
  osrm-data/     локальные данные OSRM, не загружаются в GitHub
```

Проект состоит из четырех основных частей:

```text
1. PostgreSQL — база данных с городами, тарифами, зонами и расчётами.
2. Backend — FastAPI-приложение, которое выполняет расчёт.
3. Frontend — React-интерфейс для пользователя.
4. OSRM — локальный сервис маршрутизации по данным OpenStreetMap.
```

---

## Технологии

### Backend

- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- Pydantic
- httpx
- Uvicorn

### Frontend

- React
- Vite
- Axios
- CSS

### Routing

- OSRM, Open Source Routing Machine
- OpenStreetMap data

### Infrastructure

- Docker Desktop
- PostgreSQL локально
- OSRM локально
- PowerShell-скрипты для запуска

---

## Структура проекта

```text
transport-calc/
  backend/
    app/
      main.py
      config.py
      database.py
      models.py
      schemas.py

      routers/
        cities.py
        calculate.py
        calculations.py
        locations.py
        osrm.py

      services/
        calculator.py
        osrm.py

    .env
    .env.example
    requirements.txt

  frontend/
    src/
      App.jsx
      App.css
      main.jsx
      index.css

    .env
    .env.example
    package.json

  osrm-data/
    russia-latest.osm.pbf
    russia-latest.osrm
    ...

  start_backend.ps1
  start_frontend.ps1
  README.md
  .gitignore
```

---

## Как работает расчёт

Алгоритм расчёта:

```text
1. Пользователь выбирает город отправления и город назначения.
2. Frontend отправляет from_city_id, to_city_id и параметры груза.
3. Backend находит города в таблице cities.
4. Backend определяет тарифные зоны городов.
5. Backend ищет тарифное направление:
   - сначала city_to_zone;
   - если не найдено, zone_to_zone.
6. Backend ищет подходящий тариф:
   - по направлению;
   - по максимальной длине;
   - по максимальной ширине;
   - по максимальной высоте;
   - по максимальному весу.
7. Backend ищет расстояние в distance_cache.
8. Если расстояние найдено, backend использует его.
9. Если расстояния нет, backend обращается к OSRM.
10. OSRM возвращает дорожное расстояние.
11. Backend сохраняет расстояние в distance_cache.
12. Backend считает стоимость.
13. Backend сохраняет расчёт в calculations.
14. Frontend показывает результат пользователю.
```

Формула расчёта:

```text
base_price = distance_km × rate_per_km
final_price = base_price + border_crossing_price
```
