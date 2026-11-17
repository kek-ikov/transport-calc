# Краткая инструкция по запуску калькулятора перевозки

## Что нужно установить

На сервере или компьютере должны быть установлены:

```text
Python 3.12+
Node.js 20+
PostgreSQL
Docker
```

---

## База данных

Создать базу PostgreSQL:

```text
CREATE DATABASE transport_calc
```

Восстановить переданный SQL-дамп.

После восстановления выполнить:

```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

Если индексы для поиска городов не были добавлены вместе с дампом, выполните:

```sql
CREATE INDEX IF NOT EXISTS idx_cities_name_trgm 
ON cities 
USING gin (name gin_trgm_ops); 

CREATE INDEX IF NOT EXISTS idx_cities_normalized_name_trgm 
ON cities 
USING gin (normalized_name gin_trgm_ops);
```


---

## Backend

Перейти в папку backend:

```bash
cd backend
```

Создать виртуальное окружение:

```bash
python -m venv .venv
```

Активировать его:

```powershell
.venv\Scripts\Activate.ps1
```

Установить зависимости:

```bash
pip install -r requirements.txt
```

Создать файл `.env` в папке `backend`:

```env
DATABASE_URL=postgresql+psycopg2://postgres:password@localhost:5432/transport_calc
OSRM_BASE_URL=http://127.0.0.1:5000
```

Заменить `postgres`, `password` и `transport_calc` на свои данные.

---

## OSRM

OSRM уже подготовлен и находится в папке:

```text
osrm-data/
```

Запустить OSRM из корня проекта:

```powershell
docker run -t -i -p 5000:5000 -v "${PWD}\osrm-data:/data" osrm/osrm-backend osrm-routed --algorithm mld /data/russia-latest.osrm
```

OSRM должен быть доступен по адресу:

```text
http://127.0.0.1:5000
```

---

## Запуск backend

В отдельном терминале:

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Проверка:

```text
http://127.0.0.1:8000/docs
```

---

## Frontend

Перейти в папку frontend:

```bash
cd frontend
```

Установить зависимости:

```bash
npm install
```

Запустить frontend:

```bash
npm run dev
```

Открыть:

```text
http://localhost:5173
```

## Сервер и Git

Рабочая ветка: optimize-memory-and-routing.
Каталог на сервере: /opt/transport-calc-git. Compose project: transport-calc.
.env, карты, SQL-дампы и резервные копии не хранятся в Git.

Обновление после локальных тестов и git push:

```sh
cd /opt/transport-calc-git
git pull --ff-only origin optimize-memory-and-routing
docker compose -p transport-calc up -d --build
sh scripts/memory-check.sh
```

Точка отката: baseline-before-optimization-20261117.
Перед откатом сохранить текущую БД. Затем git switch --detach baseline-before-optimization-20261117
и docker compose -p transport-calc up -d --build. Добавленный индекс совместим со старым кодом;
при необходимости его удаляет migrations/001_directional_cache_down.sql.
Резервная копия до оптимизации: /opt/transport-calc/backups/pre-optimization.dump.
Git не заменяет резервную копию БД. Не использовать docker compose down -v.

Проверки: python -m unittest discover -s backend/tests (PYTHONPATH=backend и DATABASE_URL обязательны),
npm --prefix frontend run build. memory-check.sh возвращает ошибку при доступной памяти ниже 15%.

### Аудит БД 17.11.2026

12 таблиц, около 2.6 МБ вместе с индексами. Удаление таблиц не решает потребление RAM.
Добавлен составной индекс направленного кеша; исключено использование обратного расстояния.
Сохранены справочники и связи зон: они определяют приоритет отдельных тарифов.
Кандидат на отдельную миграцию: перенос regional_rates.json в единую таблицу коротких тарифов
с габаритными ограничениями и допускаемой пустой ценой, замена fixed_distance_tariffs.
До завершения такой миграции старую таблицу не удалять. История расчетов может быть очищена
по согласованию, но экономия при 41 записи несущественна.

Замер после mmap: OSRM около 711 МиБ после 20 запросов (4 параллельно), доступно 6.93 ГиБ.
Первый маршрут 1.675 с, повторный 0.049 с. Это короткая проверка, не длительный нагрузочный тест.
