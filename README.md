# Transport Calculator

Прототип калькулятора стоимости перевозки.

Проект рассчитывает стоимость маршрута на основе:

- города отправления;
- города назначения;
- габаритов груза;
- веса груза;
- тарифных зон;
- тарифных направлений;
- дорожного расстояния, рассчитанного через OSRM.

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

## Архитектура проекта

Общая схема работы:

```text
React Frontend
      ↓
FastAPI Backend
      ↓
PostgreSQL
      ↓
OSRM local server
```

Более подробно:

```text
Пользователь
   ↓
React Frontend
   ↓
POST /calculate
   ↓
FastAPI Backend
   ↓
PostgreSQL:
  - cities
  - federal_subjects
  - tariff_zones
  - tariff_directions
  - tariffs
  - distance_cache
  - calculations
   ↓
OSRM:
  - если расстояния нет в distance_cache
   ↓
Backend считает стоимость
   ↓
Frontend показывает результат
```

Frontend отвечает только за интерфейс:

```text
- выбор города отправления;
- выбор города назначения;
- ввод габаритов груза;
- ввод веса;
- отправку запроса на backend;
- отображение результата;
- отображение истории расчётов.
```

Backend отвечает за бизнес-логику:

```text
- поиск городов;
- определение тарифных зон;
- подбор тарифного направления;
- подбор подходящего тарифа;
- получение расстояния;
- обращение к OSRM;
- сохранение кэша расстояний;
- сохранение истории расчётов;
- возврат результата во frontend.
```

OSRM отвечает только за маршрутизацию:

```text
координаты точки А → координаты точки Б → дорожное расстояние
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

## Основные возможности

На текущем этапе проект умеет:

```text
- искать города;
- выбирать город отправления;
- выбирать город назначения;
- проверять наличие координат;
- рассчитывать расстояние по дорогам через OSRM;
- кэшировать расстояния в distance_cache;
- определять тарифную зону города;
- искать тарифное направление;
- подбирать подходящий тариф по габаритам и весу;
- считать итоговую стоимость перевозки;
- сохранять расчёт в calculations;
- показывать историю последних расчётов;
- работать через React-интерфейс.
```

---

## Требования для запуска

Перед запуском нужно установить:

```text
Python 3.12+
Node.js LTS
PostgreSQL
Docker Desktop
Git
```
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

## Запуск проекта

Для полноценной работы нужно запустить три процесса.

В первом окне терминала (OSRM):

```powershell
cd \transport-calc\osrm-data
docker run -t -i -p 5000:5000 -v "${PWD}:/data" osrm/osrm-backend osrm-routed --algorithm mld /data/russia-latest.osrm
```

Во втором окне терминала (backend):

```powershell
cd \transport-calc
.\start_backend.ps1
```

В третьем окне терминала (frontend):

```powershell
cd C:\Users\user\projects\transport-calc
.\start_frontend.ps1
```

После запуска открыть сайт:

```text
http://localhost:5173
```

ОПЦИОНАЛЬНО создать ссылку на сайт, чтобы по ней могли перейти другие:

```text
npx localtunnel --port 8000
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
