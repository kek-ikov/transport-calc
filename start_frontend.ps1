Set-Location "$PSScriptRoot\frontend"

if (-Not (Test-Path "node_modules")) {
    Write-Host "node_modules не найден. Устанавливаю зависимости frontend..."
    npm install
}

Write-Host "Запускаю React frontend..."
npm run dev