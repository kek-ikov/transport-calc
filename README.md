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

```text
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
