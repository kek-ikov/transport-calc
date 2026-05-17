Set-Location "$PSScriptRoot\backend"

if (-Not (Test-Path ".venv")) {
    Write-Host "Виртуальное окружение не найдено. Создаю .venv..."
    python -m venv .venv
}

Write-Host "Активирую виртуальное окружение..."
& ".\.venv\Scripts\Activate.ps1"

Write-Host "Устанавливаю зависимости backend..."
pip install -r requirements.txt

Write-Host "Запускаю FastAPI backend..."
uvicorn app.main:app --reload